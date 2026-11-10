# Standard library

Quill ships a few modules in the `std/` folder. Bring them in like any other
module; no `quill.pkg` entry is needed:

```python
bring std.math
bring std.random
bring std.stats
```

Errors (bad arguments, empty lists) are thrown as `Error`, so they can be caught
with `try`/`catch`. The built-in `List`, `Map` and `Set` need no `bring`; see the
language guide.

## std.math: `Math`

All static methods. Float functions also accept ints. Functions that work on ints
only start with `i`.

| Group | Methods |
|---|---|
| Constants | `pi()`, `e()`, `tau()` |
| Sign and extremes | `abs`, `iabs`, `sign`, `isign`, `min`, `max`, `imin`, `imax`, `clamp`, `iclamp`, `lerp` |
| Rounding | `floor`, `ceil`, `round`, `trunc` (results stay `float`; use `int(x)`) |
| Powers and logs | `sqrt`, `cbrt`, `pow`, `hypot`, `exp`, `ln`, `log10`, `log2`, `logBase` |
| Trigonometry | `sin`, `cos`, `tan`, `asin`, `acos`, `atan`, `atan2`, `sinh`, `cosh`, `tanh`, `toRadians`, `toDegrees` |
| Float checks | `isNaN`, `isInfinite` |
| Integers | `ipow`, `mod` (sign of the divisor), `gcd`, `lcm`, `isqrt`, `isPrime`, `factorial` (0 to 20), `fib` (0 to 92) |

```python
print(Math.sqrt(2.0), Math.gcd(12, 18), Math.mod(-1, 5))
```

## std.random: `Random`

A seedable generator: the same seed gives the same sequence on every platform.
Not for security.

```python
r = new Random(42)
r.next()            # 0 .. 2147483647
r.nextInt(10)       # 0 <= n < 10
r.between(-3, 3)    # -3 <= n <= 3
r.nextFloat()       # 0.0 <= f < 1.0
r.nextBool()
r.index(list.size())
```

## std.stats: `Stats`

Population statistics. The float versions take `List[float]`; the `i` versions
take `List[int]`. An empty list throws an `Error`. Inputs are never modified.

`sum`, `mean`, `median`, `variance`, `stddev`, `range`, `isum`, `imean`, `imedian`

## Bytes, hashing and encryption

These modules work on **bytes**, written as `List[int]` with each element 0..255.
A Quill string never contains a zero byte, so binary data (digests, ciphertext)
is shown as text with `Hex` or `Base64`.

```python
bring std.text
bring std.encoding
bring std.hash
bring std.cipher
bring std.crypto
```

### std.text: `Text`

| Method | Result |
|---|---|
| `Text.bytes(s)` | the bytes of a string |
| `Text.fromBytes(bs)` | a string from bytes; throws if a byte is 0 or over 255 |
| `Text.byteAt(s, i)` | one byte, bounds checked |
| `Text.chr(code)` | a one-byte string, code 1..255 |

### std.encoding: `Hex`, `Base64`

`Hex.encode(bs)`, `Hex.decode(s)` (either case), `Base64.encode(bs)` (with `=`
padding) and `Base64.decode(s)`. Malformed text throws an `Error`.

### std.hash: `Hash`

| Method | Result |
|---|---|
| `sha256(bs)`, `sha512(bs)` | digest as 32 / 64 bytes |
| `sha256Hex(text)`, `sha512Hex(text)` | digest of a string as hex |
| `crc32(bs)` | the zip/png checksum, 0..4294967295 (not a secure hash) |
| `hmacSha256(key, message)` | keyed hash (bytes), to authenticate a message |
| `pbkdf2(password, salt, iterations, length)` | PBKDF2-HMAC-SHA256 key stretching |

```python
print(Hash.sha256Hex("abc"))
# ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad
```

### std.cipher: `Aes`, `Cipher`

Building blocks. These give confidentiality only and do not detect tampering;
prefer `std.crypto` unless you need a specific format.

- `new Aes(key)` with a 16, 24 or 32 byte key, then `encryptBlock(b)` and
  `decryptBlock(b)` on 16-byte blocks.
- `Cipher.aesCbcEncrypt(key, iv, data)` / `aesCbcDecrypt`: CBC with PKCS#7 padding,
  16-byte iv, a different unpredictable iv for every message.
- `Cipher.aesCtr(key, nonce16, data)`: counter mode; the same call decrypts.
- `Cipher.chacha20(key32, nonce12, counter, data)`: RFC 8439; the same call decrypts.
- `Cipher.xorBytes(data, key)`: repeating-key XOR. Masking, not secrecy.
- `Cipher.slice(xs, from, count)`: a sub-list.

Never reuse a (key, nonce) pair in CTR or ChaCha20.

### std.crypto: `Crypto`

The safe interface.

```python
token = Crypto.encrypt("correct horse", "attack at dawn")   # text, safe to store
Crypto.decrypt("correct horse", token)                      # "attack at dawn"

key = Crypto.generateKey(32)
box = Crypto.seal(key, Text.bytes("secret"))                # AES-CTR + HMAC, encrypt-then-MAC
Text.fromBytes(Crypto.open(key, box))                       # throws Error if the key is wrong
                                                            # or a single bit was changed

stored = Crypto.hashPassword("hunter2")                     # "iterations$salt$hash"
Crypto.checkPassword("hunter2", stored)                     # true
```

- `seal` / `open` derive separate encryption and MAC keys from your key, use a
  fresh random iv, and verify the tag in constant time before decrypting.
- `encrypt` / `decrypt` stretch the password with PBKDF2 (20000 iterations by
  default; `encryptWith(password, text, n)` and `hashPasswordWith(password, n)`
  choose another count, which is stored in the output).
- `randomBytes(n)` and `randomInt(bound)` use the operating system's secure
  random source. `std.random` does not; never use it for keys.
- `Crypto.equals(a, b)` compares byte lists in constant time.

**Be honest about the limits.** These are straightforward implementations
checked against the published test vectors (FIPS-197, RFC 8439, RFC 4231 style
HMAC, PBKDF2) and OpenSSL, but they have not been audited, are not hardened
against side channels such as cache timing, and are much slower than OpenSSL. They are
fine for learning, tools and moderate-stakes data; for anything critical use a
vetted library.

## Notes

- `Math`, `Random` and `Stats` are plain class names. If your own code uses the
  same names, bring the module under an alias (`bring std.math as m`, then
  `m.Math`).
- A local module or a package named `std` takes precedence over the bundled one.
