// ---------------------------------------------------------------------------
// ProgramError — mirrors the Rust ProgramError enum
// ---------------------------------------------------------------------------

export type ProgramError =
  | { type: "InvalidArgument" }
  | { type: "InvalidInstructionData" }
  | { type: "InvalidAccountData" }
  | { type: "AccountDataTooSmall" }
  | { type: "InsufficientFunds" }
  | { type: "IncorrectProgramId" }
  | { type: "MissingRequiredSignature" }
  | { type: "AccountAlreadyInitialized" }
  | { type: "UninitializedAccount" }
  | { type: "MissingAccount" }
  | { type: "InvalidSeeds" }
  | { type: "ArithmeticOverflow" }
  | { type: "AccountNotRentExempt" }
  | { type: "InvalidAccountOwner" }
  | { type: "IncorrectAuthority" }
  | { type: "Immutable" }
  | { type: "BorshIoError" }
  | { type: "ComputeBudgetExceeded" }
  | { type: "Custom"; code: number }
  | { type: "Runtime"; message: string };

/** Map a wire status code + error message into a ProgramError. */
export function programErrorFromStatus(
  status: number,
  errorMessage: string | null
): ProgramError {
  // status > 0 → Custom(n) from the program
  if (status > 0) return { type: "Custom", code: status };

  // status < 0 → known runtime/instruction error
  switch (status) {
    case -2: return { type: "InvalidArgument" };
    case -3: return { type: "InvalidInstructionData" };
    case -4: return { type: "InvalidAccountData" };
    case -5: return { type: "AccountDataTooSmall" };
    case -6: return { type: "InsufficientFunds" };
    case -7: return { type: "IncorrectProgramId" };
    case -8: return { type: "MissingRequiredSignature" };
    case -9: return { type: "AccountAlreadyInitialized" };
    case -10: return { type: "UninitializedAccount" };
    case -11: return { type: "MissingAccount" };
    case -12: return { type: "ComputeBudgetExceeded" };
    case -13: return { type: "ArithmeticOverflow" };
    default: return { type: "Runtime", message: errorMessage ?? "unknown error" };
  }
}

// ---------------------------------------------------------------------------
// ExecutionStatus — discriminated union for pattern matching
// ---------------------------------------------------------------------------

export type ExecutionStatus =
  | { ok: true }
  | { ok: false; error: ProgramError };

// ---------------------------------------------------------------------------
// ExecutionResult
// ---------------------------------------------------------------------------

export interface ExecutionResult<TAccount> {
  status: ExecutionStatus;
  computeUnits: bigint;
  executionTimeUs: bigint;
  returnData: Uint8Array;
  accounts: TAccount[];
  logs: string[];
}

export interface Clock {
  slot: bigint;
  epochStartTimestamp: bigint;
  epoch: bigint;
  leaderScheduleEpoch: bigint;
  unixTimestamp: bigint;
}

export interface EpochSchedule {
  slotsPerEpoch: bigint;
  leaderScheduleSlotOffset: bigint;
  warmup: boolean;
  firstNormalEpoch: bigint;
  firstNormalSlot: bigint;
}
