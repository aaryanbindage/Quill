# std.cipher and std.crypto against OpenSSL / FIPS-197 / RFC 8439 vectors
bring std.text
bring std.encoding
bring std.hash
bring std.cipher
bring std.crypto

class Main:
    static def check(name: str, ok: bool):
        if ok:
            print("ok  ", name)
        else:
            print("FAIL", name)

    static def seq(n: int) -> List[int]:
        out = new List[int]()
        for i in range(n):
            out.add(i)
        return out

    static def main():
        base: int = heap_live()

        pt = Hex.decode("00112233445566778899aabbccddeeff")

        a128 = new Aes(Main.seq(16))
        Main.check("aes-128 block", Hex.encode(a128.encryptBlock(pt)) == "69c4e0d86a7b0430d8cdb78070b4c55a")
        Main.check("aes-128 inverse", Hex.encode(a128.decryptBlock(a128.encryptBlock(pt))) == "00112233445566778899aabbccddeeff")
        a192 = new Aes(Main.seq(24))
        Main.check("aes-192 block", Hex.encode(a192.encryptBlock(pt)) == "dda97ca4864cdfe06eaf70a0ec0d7191")
        Main.check("aes-192 inverse", Hex.encode(a192.decryptBlock(Hex.decode("dda97ca4864cdfe06eaf70a0ec0d7191"))) == "00112233445566778899aabbccddeeff")
        a256 = new Aes(Main.seq(32))
        Main.check("aes-256 block", Hex.encode(a256.encryptBlock(pt)) == "8ea2b7ca516745bfeafc49904b496089")
        Main.check("aes-256 inverse", Hex.encode(a256.decryptBlock(Hex.decode("8ea2b7ca516745bfeafc49904b496089"))) == "00112233445566778899aabbccddeeff")

        msg = Text.bytes("The quick brown fox jumps over the lazy dog")
        iv = Hex.decode("0f0e0d0c0b0a09080706050403020100")
        c128 = Cipher.aesCbcEncrypt(Main.seq(16), iv, msg)
        Main.check("cbc-128", Hex.encode(c128) == "6f40de04ce96f3426280fc4c87d9209aa2112afaf1970696d85445e1ff6817db4b32306ba0028ebe4202250343a631f5")
        Main.check("cbc-128 decrypt", Text.fromBytes(Cipher.aesCbcDecrypt(Main.seq(16), iv, c128)) == "The quick brown fox jumps over the lazy dog")
        c256 = Cipher.aesCbcEncrypt(Main.seq(32), iv, msg)
        Main.check("cbc-256", Hex.encode(c256) == "925c81ee81fae7d66040fade898963245afeab7af7697a0762fe3f72ebfe8a357f559f086177f447d1b11bd60d670c35")
        Main.check("cbc empty", Cipher.aesCbcDecrypt(Main.seq(16), iv, Cipher.aesCbcEncrypt(Main.seq(16), iv, new List[int]())).size() == 0)
        Main.check("cbc exact block", Cipher.aesCbcEncrypt(Main.seq(16), iv, Main.seq(16)).size() == 32)
        msgs = ""
        try:
            Cipher.aesCbcDecrypt(Main.seq(32), iv, c128)
        catch Error as e:
            msgs = e.message
        Main.check("cbc wrong key", msgs == "aesCbcDecrypt: bad padding (wrong key or corrupted data)" or msgs == "")
        msgs = ""
        try:
            Cipher.aesCbcDecrypt(Main.seq(16), iv, Main.seq(10))
        catch Error as e:
            msgs = e.message
        Main.check("cbc bad length", msgs == "aesCbcDecrypt: ciphertext must be a non-empty multiple of 16 bytes")

        Main.check("ctr-192", Hex.encode(Cipher.aesCtr(Main.seq(24), iv, msg)) == "7ecf4400be2dec9879b6cd0235fcd9b84a1e1053f2808ee55da00f3326791c31df5cccc79de440613843dd")
        ff = Hex.decode("ffffffffffffffffffffffffffffffff")
        Main.check("ctr counter carry", Hex.encode(Cipher.aesCtr(Main.seq(16), ff, msg)) == "682c7a12bf72eb400ff7c0eb6127d533a0ce4317edfa36f21c6fee14c4baf80d1b2333f9f4bacd3e2d14da")
        Main.check("ctr round trip", Text.fromBytes(Cipher.aesCtr(Main.seq(24), iv, Cipher.aesCtr(Main.seq(24), iv, msg))) == "The quick brown fox jumps over the lazy dog")

        plain = Text.bytes("Ladies and Gentlemen of the class of '99: If I could offer you only one tip for the future, sunscreen would be it.")
        nonce = Hex.decode("000000000000004a00000000")
        cc = Cipher.chacha20(Main.seq(32), nonce, 1, plain)
        Main.check("chacha20 rfc8439", Hex.encode(cc) == "6e2e359a2568f98041ba0728dd0d6981e97e7aec1d4360c20a27afccfd9fae0bf91b65c5524733ab8f593dabcd62b3571639d624e65152ab8f530c359f0861d807ca0dbf500d6a6156a38e088a22b65e52bc514d16ccf806818ce91ab77937365af90bbf74a35be6b40b8eedf2785e42874d")
        Main.check("chacha20 round trip", Hex.encode(Cipher.chacha20(Main.seq(32), nonce, 1, cc)) == Hex.encode(plain))
        Main.check("xor", Hex.encode(Cipher.xorBytes([1, 2, 3, 4, 5], [255, 15])) == "fe0dfc0bfa" and Cipher.xorBytes(Cipher.xorBytes(msg, [7, 9]), [7, 9]).size() == msg.size())

        r = Crypto.randomBytes(32)
        Main.check("randomBytes", r.size() == 32 and Crypto.randomBytes(0).size() == 0 and not Crypto.equals(r, Crypto.randomBytes(32)))
        ok = true
        for i in range(500):
            x = Crypto.randomInt(10)
            if x < 0 or x >= 10:
                ok = false
        Main.check("randomInt", ok)
        Main.check("equals", Crypto.equals([1, 2, 3], [1, 2, 3]) and not Crypto.equals([1, 2, 3], [1, 2, 4]) and not Crypto.equals([1, 2], [1, 2, 3]))

        key = Crypto.generateKey(32)
        box = Crypto.seal(key, msg)
        Main.check("seal size", box.size() == 16 + msg.size() + 32)
        Main.check("open", Text.fromBytes(Crypto.open(key, box)) == "The quick brown fox jumps over the lazy dog")
        Main.check("seal is randomized", not Crypto.equals(box, Crypto.seal(key, msg)))
        tampered = box.copy()
        tampered.set(20, tampered.get(20) ^ 1)
        msgs = ""
        try:
            Crypto.open(key, tampered)
        catch Error as e:
            msgs = e.message
        Main.check("tamper detected", msgs == "open: authentication failed (wrong key or tampered data)")
        msgs = ""
        try:
            Crypto.open(Crypto.generateKey(32), box)
        catch Error as e:
            msgs = e.message
        Main.check("wrong key detected", msgs == "open: authentication failed (wrong key or tampered data)")

        token = Crypto.encryptWith("correct horse", "attack at dawn", 500)
        Main.check("encrypt/decrypt", Crypto.decrypt("correct horse", token) == "attack at dawn")
        msgs = ""
        try:
            Crypto.decrypt("wrong horse", token)
        catch Error as e:
            msgs = e.message
        Main.check("wrong password", msgs == "open: authentication failed (wrong key or tampered data)")
        Main.check("default iterations", Crypto.decrypt("pw", Crypto.encrypt("pw", "x")) == "x")
        stored = Crypto.hashPasswordWith("hunter2", 500)
        Main.check("password hash", Crypto.checkPassword("hunter2", stored) and not Crypto.checkPassword("hunter3", stored) and not Crypto.checkPassword("x", "garbage"))

        msgs = null
        token = null
        stored = null
        pt = null
        a128 = null
        a192 = null
        a256 = null
        msg = null
        iv = null
        c128 = null
        c256 = null
        ff = null
        plain = null
        nonce = null
        cc = null
        r = null
        key = null
        box = null
        tampered = null
        if heap_live() - base == 0:
            print("ok   no leaks")
        else:
            print("LEAK", heap_live() - base)
