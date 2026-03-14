// ---------------------------------------------------------------------------
// SPL Token types and binary packing (no external deps)
// ---------------------------------------------------------------------------

/** Default Solana rent: minimum_balance(data_len) = (data_len + 128) * 3480 * 2 */
export function rentMinimumBalance(dataLen: number): bigint {
  return BigInt(dataLen + 128) * 3480n * 2n;
}

export interface MintData {
  mintAuthority?: Uint8Array; // 32-byte pubkey
  supply?: bigint;
  decimals?: number;
  freezeAuthority?: Uint8Array; // 32-byte pubkey
}

export interface TokenAccountData {
  mint: Uint8Array; // 32-byte pubkey
  owner: Uint8Array; // 32-byte pubkey
  amount: bigint;
  delegate?: Uint8Array; // 32-byte pubkey
  state?: TokenAccountState;
  isNative?: bigint;
  delegatedAmount?: bigint;
  closeAuthority?: Uint8Array; // 32-byte pubkey
}

export enum TokenAccountState {
  Uninitialized = 0,
  Initialized = 1,
  Frozen = 2,
}

export const MINT_LEN = 82;
export const TOKEN_ACCOUNT_LEN = 165;

export function packMint(mint: MintData): Buffer {
  const buf = Buffer.alloc(MINT_LEN);
  let o = 0;

  // COption<Pubkey> mint_authority
  o = packCOptionPubkey(buf, o, mint.mintAuthority);
  // u64 supply
  buf.writeBigUInt64LE(mint.supply ?? 0n, o);
  o += 8;
  // u8 decimals
  buf[o] = mint.decimals ?? 9;
  o += 1;
  // bool is_initialized
  buf[o] = 1;
  o += 1;
  // COption<Pubkey> freeze_authority
  o = packCOptionPubkey(buf, o, mint.freezeAuthority);

  return buf;
}

export function packTokenAccount(token: TokenAccountData): Buffer {
  const buf = Buffer.alloc(TOKEN_ACCOUNT_LEN);
  let o = 0;

  // Pubkey mint
  Buffer.from(token.mint).copy(buf, o);
  o += 32;
  // Pubkey owner
  Buffer.from(token.owner).copy(buf, o);
  o += 32;
  // u64 amount
  buf.writeBigUInt64LE(token.amount, o);
  o += 8;
  // COption<Pubkey> delegate
  o = packCOptionPubkey(buf, o, token.delegate);
  // u8 state
  buf[o] = token.state ?? TokenAccountState.Initialized;
  o += 1;
  // COption<u64> is_native
  o = packCOptionU64(buf, o, token.isNative);
  // u64 delegated_amount
  buf.writeBigUInt64LE(token.delegatedAmount ?? 0n, o);
  o += 8;
  // COption<Pubkey> close_authority
  o = packCOptionPubkey(buf, o, token.closeAuthority);

  return buf;
}

// ---------------------------------------------------------------------------
// Unpack
// ---------------------------------------------------------------------------

export function unpackMint(data: Uint8Array): MintData | null {
  if (data.length < MINT_LEN) return null;
  const buf = Buffer.from(data);
  let o = 0;
  const [mintAuthority, o1] = unpackCOptionPubkey(buf, o); o = o1;
  const supply = buf.readBigUInt64LE(o); o += 8;
  const decimals = buf[o]; o += 1;
  const isInitialized = buf[o] !== 0; o += 1;
  if (!isInitialized) return null;
  const [freezeAuthority, o2] = unpackCOptionPubkey(buf, o); o = o2;
  return { mintAuthority: mintAuthority ?? undefined, supply, decimals, freezeAuthority: freezeAuthority ?? undefined };
}

export function unpackTokenAccount(data: Uint8Array): TokenAccountData | null {
  if (data.length < TOKEN_ACCOUNT_LEN) return null;
  const buf = Buffer.from(data);
  let o = 0;
  const mint = new Uint8Array(buf.subarray(o, o + 32)); o += 32;
  const owner = new Uint8Array(buf.subarray(o, o + 32)); o += 32;
  const amount = buf.readBigUInt64LE(o); o += 8;
  const [delegate, o1] = unpackCOptionPubkey(buf, o); o = o1;
  const stateVal = buf[o]; o += 1;
  const state = stateVal as TokenAccountState;
  const [isNativeRaw, o2] = unpackCOptionU64(buf, o); o = o2;
  const delegatedAmount = buf.readBigUInt64LE(o); o += 8;
  const [closeAuthority, o3] = unpackCOptionPubkey(buf, o); o = o3;
  return {
    mint, owner, amount,
    delegate: delegate ?? undefined,
    state,
    isNative: isNativeRaw ?? undefined,
    delegatedAmount,
    closeAuthority: closeAuthority ?? undefined,
  };
}

function unpackCOptionPubkey(buf: Buffer, offset: number): [Uint8Array | null, number] {
  const tag = buf.readUInt32LE(offset);
  const key = new Uint8Array(buf.subarray(offset + 4, offset + 36));
  return [tag === 1 ? key : null, offset + 36];
}

function unpackCOptionU64(buf: Buffer, offset: number): [bigint | null, number] {
  const tag = buf.readUInt32LE(offset);
  const val = buf.readBigUInt64LE(offset + 4);
  return [tag === 1 ? val : null, offset + 12];
}

// ---------------------------------------------------------------------------
// Instruction builders
// ---------------------------------------------------------------------------

export function tokenTransferData(amount: bigint): Buffer {
  const buf = Buffer.alloc(9);
  buf[0] = 3; // Transfer
  buf.writeBigUInt64LE(amount, 1);
  return buf;
}

export function tokenMintToData(amount: bigint): Buffer {
  const buf = Buffer.alloc(9);
  buf[0] = 7; // MintTo
  buf.writeBigUInt64LE(amount, 1);
  return buf;
}

export function tokenBurnData(amount: bigint): Buffer {
  const buf = Buffer.alloc(9);
  buf[0] = 8; // Burn
  buf.writeBigUInt64LE(amount, 1);
  return buf;
}

// ---------------------------------------------------------------------------
// Pack helpers
// ---------------------------------------------------------------------------

function packCOptionPubkey(
  buf: Buffer,
  offset: number,
  key?: Uint8Array
): number {
  if (key) {
    buf.writeUInt32LE(1, offset);
    Buffer.from(key).copy(buf, offset + 4);
  } else {
    buf.writeUInt32LE(0, offset);
  }
  return offset + 36;
}

function packCOptionU64(
  buf: Buffer,
  offset: number,
  val?: bigint
): number {
  if (val !== undefined) {
    buf.writeUInt32LE(1, offset);
    buf.writeBigUInt64LE(val, offset + 4);
  } else {
    buf.writeUInt32LE(0, offset);
  }
  return offset + 12;
}
