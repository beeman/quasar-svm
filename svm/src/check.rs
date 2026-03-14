use solana_account::Account;
use solana_pubkey::Pubkey;
use solana_rent::Rent;

use crate::error::ProgramError;
use crate::svm::ExecutionResult;

/// Declarative check for validating an `ExecutionResult`.
///
/// ```ignore
/// use quasar_svm::{Check, ProgramError};
///
/// svm.process_and_validate_transaction(
///     &[ix],
///     &accounts,
///     &[
///         Check::success(),
///         Check::compute_units(1_200),
///         Check::account(&key)
///             .lamports(1_000_000)
///             .owner(&program_id)
///             .build(),
///     ],
/// );
/// ```
pub enum Check<'a> {
    /// Assert that execution succeeded.
    Success,
    /// Assert that execution failed with a specific `ProgramError`.
    Err(ProgramError),
    /// Assert that compute units consumed equals this value.
    ComputeUnits(u64),
    /// Assert return data matches.
    ReturnData(&'a [u8]),
    /// Assert properties of a resulting account.
    Account(AccountCheck<'a>),
}

impl<'a> Check<'a> {
    pub const fn success() -> Self {
        Self::Success
    }

    pub const fn err(error: ProgramError) -> Self {
        Self::Err(error)
    }

    pub const fn compute_units(units: u64) -> Self {
        Self::ComputeUnits(units)
    }

    pub const fn return_data(data: &'a [u8]) -> Self {
        Self::ReturnData(data)
    }

    /// Start building an account check.
    pub const fn account(pubkey: &'a Pubkey) -> AccountCheckBuilder<'a> {
        AccountCheckBuilder {
            pubkey,
            lamports: None,
            data: None,
            data_slice: None,
            owner: None,
            space: None,
            closed: false,
            rent_exempt: false,
        }
    }
}

/// Builder for account property assertions.
pub struct AccountCheckBuilder<'a> {
    pubkey: &'a Pubkey,
    lamports: Option<u64>,
    data: Option<&'a [u8]>,
    data_slice: Option<(usize, &'a [u8])>,
    owner: Option<&'a Pubkey>,
    space: Option<usize>,
    closed: bool,
    rent_exempt: bool,
}

impl<'a> AccountCheckBuilder<'a> {
    pub const fn lamports(mut self, lamports: u64) -> Self {
        self.lamports = Some(lamports);
        self
    }

    pub const fn data(mut self, data: &'a [u8]) -> Self {
        self.data = Some(data);
        self
    }

    pub const fn data_slice(mut self, offset: usize, data: &'a [u8]) -> Self {
        self.data_slice = Some((offset, data));
        self
    }

    pub const fn owner(mut self, owner: &'a Pubkey) -> Self {
        self.owner = Some(owner);
        self
    }

    pub const fn space(mut self, space: usize) -> Self {
        self.space = Some(space);
        self
    }

    pub const fn closed(mut self) -> Self {
        self.closed = true;
        self
    }

    pub const fn rent_exempt(mut self) -> Self {
        self.rent_exempt = true;
        self
    }

    pub const fn build(self) -> Check<'a> {
        Check::Account(AccountCheck {
            pubkey: self.pubkey,
            lamports: self.lamports,
            data: self.data,
            data_slice: self.data_slice,
            owner: self.owner,
            space: self.space,
            closed: self.closed,
            rent_exempt: self.rent_exempt,
        })
    }
}

pub struct AccountCheck<'a> {
    pub pubkey: &'a Pubkey,
    pub lamports: Option<u64>,
    pub data: Option<&'a [u8]>,
    pub data_slice: Option<(usize, &'a [u8])>,
    pub owner: Option<&'a Pubkey>,
    pub space: Option<usize>,
    pub closed: bool,
    pub rent_exempt: bool,
}

// ---------------------------------------------------------------------------
// Validation
// ---------------------------------------------------------------------------

/// Run checks against a result. Returns a list of failure messages.
/// Empty list means all checks passed.
pub fn run_checks(result: &ExecutionResult, checks: &[Check], rent: &Rent) -> Vec<String> {
    let mut failures = Vec::new();

    for check in checks {
        match check {
            Check::Success => {
                if let Some(err) = result.error() {
                    failures.push(format!("expected success, got error: {err}"));
                }
            }
            Check::Err(expected) => match result.error() {
                Some(ref actual) if actual == expected => {}
                Some(actual) => {
                    failures.push(format!("expected error {expected:?}, got {actual:?}"));
                }
                None => {
                    failures.push(format!(
                        "expected error {expected:?}, but execution succeeded"
                    ));
                }
            },
            Check::ComputeUnits(expected) => {
                let actual = result.compute_units_consumed;
                if actual != *expected {
                    failures.push(format!(
                        "compute units: expected {expected}, got {actual} (delta: {:+})",
                        actual as i64 - *expected as i64
                    ));
                }
            }
            Check::ReturnData(expected) => {
                if result.return_data != *expected {
                    failures.push(format!(
                        "return data: expected {} bytes, got {} bytes",
                        expected.len(),
                        result.return_data.len()
                    ));
                }
            }
            Check::Account(ac) => {
                check_account(result, ac, rent, &mut failures);
            }
        }
    }

    failures
}

fn check_account(
    result: &ExecutionResult,
    ac: &AccountCheck,
    rent: &Rent,
    failures: &mut Vec<String>,
) {
    let key_str = &ac.pubkey.to_string()[..8];

    let account = match result.account(ac.pubkey) {
        Some(a) => a,
        None => {
            failures.push(format!(
                "account {key_str}…: not found in resulting accounts"
            ));
            return;
        }
    };

    if ac.closed {
        if account.lamports != 0 || !account.data.is_empty() {
            failures.push(format!(
                "account {key_str}…: expected closed (0 lamports, empty data), got {} lamports, {} bytes",
                account.lamports,
                account.data.len()
            ));
        }
        return;
    }

    if let Some(expected) = ac.lamports {
        if account.lamports != expected {
            failures.push(format!(
                "account {key_str}…: lamports: expected {expected}, got {}",
                account.lamports
            ));
        }
    }

    if let Some(expected) = ac.data {
        if account.data != expected {
            failures.push(format!(
                "account {key_str}…: data mismatch ({} bytes expected, {} bytes actual)",
                expected.len(),
                account.data.len()
            ));
        }
    }

    if let Some((offset, expected)) = ac.data_slice {
        let end = offset + expected.len();
        if end > account.data.len() {
            failures.push(format!(
                "account {key_str}…: data_slice [{offset}..{end}] out of bounds (data is {} bytes)",
                account.data.len()
            ));
        } else if account.data[offset..end] != *expected {
            failures.push(format!(
                "account {key_str}…: data_slice [{offset}..{end}] mismatch"
            ));
        }
    }

    if let Some(expected) = ac.owner {
        if account.owner != *expected {
            failures.push(format!(
                "account {key_str}…: owner: expected {}, got {}",
                &expected.to_string()[..8],
                &account.owner.to_string()[..8]
            ));
        }
    }

    if let Some(expected) = ac.space {
        if account.data.len() != expected {
            failures.push(format!(
                "account {key_str}…: space: expected {expected}, got {}",
                account.data.len()
            ));
        }
    }

    if ac.rent_exempt {
        check_rent_exempt(account, rent, key_str, failures);
    }
}

fn check_rent_exempt(account: &Account, rent: &Rent, key_str: &str, failures: &mut Vec<String>) {
    let min = rent.minimum_balance(account.data.len());
    if account.lamports < min {
        failures.push(format!(
            "account {key_str}…: not rent-exempt ({} lamports < {min} minimum for {} bytes)",
            account.lamports,
            account.data.len()
        ));
    }
}
