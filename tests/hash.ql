# std.text, std.encoding, std.hash against published test vectors
bring std.text
bring std.encoding
bring std.hash

class Main:
    static def check(name: str, ok: bool):
        if ok:
            print("ok  ", name)
        else:
            print("FAIL", name)

    static def main():
        base: int = heap_live()

        Main.check("bytes", Text.bytes("AZ").get(0) == 65 and Text.bytes("AZ").get(1) == 90 and Text.bytes("").size() == 0)
        Main.check("fromBytes", Text.fromBytes([104, 105]) == "hi" and Text.fromBytes(Text.bytes("round trip")) == "round trip")
        Main.check("chr", Text.chr(65) == "A" and Text.byteAt("abc", 1) == 98)
        msg = ""
        try:
            Text.fromBytes([65, 0, 66])
        catch Error as e:
            msg = e.message
        Main.check("zero byte rejected", msg == "fromBytes: a string cannot hold the byte 0")

        Main.check("hex encode", Hex.encode([0, 15, 16, 255, 171]) == "000f10ffab")
        Main.check("hex decode", Hex.decode("000F10ffAB").get(3) == 255 and Hex.decode("").size() == 0)
        Main.check("hex round trip", Hex.encode(Hex.decode("deadbeef")) == "deadbeef")
        msg = ""
        try:
            Hex.decode("abc")
        catch Error as e:
            msg = e.message
        Main.check("odd hex", msg == "decode: hex text must have an even length")
        msg = ""
        try:
            Hex.decode("zz")
        catch Error as e:
            msg = e.message
        Main.check("bad hex", msg == "decode: invalid hex digit")

        Main.check("base64 empty", Base64.encode(Text.bytes("")) == "")
        Main.check("base64 f", Base64.encode(Text.bytes("f")) == "Zg==")
        Main.check("base64 fo", Base64.encode(Text.bytes("fo")) == "Zm8=")
        Main.check("base64 foo", Base64.encode(Text.bytes("foo")) == "Zm9v")
        Main.check("base64 foobar", Base64.encode(Text.bytes("foobar")) == "Zm9vYmFy")
        Main.check("base64 decode", Text.fromBytes(Base64.decode("Zm9vYmE=")) == "fooba" and Text.fromBytes(Base64.decode("Zg==")) == "f")
        Main.check("base64 binary", Hex.encode(Base64.decode(Base64.encode([0, 255, 254, 1, 128]))) == "00fffe0180")
        msg = ""
        try:
            Base64.decode("Zg=")
        catch Error as e:
            msg = e.message
        Main.check("bad base64 length", msg == "decode: base64 text must be a multiple of 4 characters")
        msg = ""
        try:
            Base64.decode("Z$==")
        catch Error as e:
            msg = e.message
        Main.check("bad base64 char", msg == "decode: invalid base64 character")

        Main.check("sha256 empty", Hash.sha256Hex("") == "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855")
        Main.check("sha256 abc", Hash.sha256Hex("abc") == "ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad")
        Main.check("sha256 two blocks", Hash.sha256Hex("abcdbcdecdefdefgefghfghighijhijkijkljklmklmnlmnomnopnopq") == "248d6a61d20638b8e5c026930c3e6039a33ce45964ff2167f6ecedd419db06c1")
        Main.check("sha256 55 bytes", Hash.sha256Hex("aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa") == "9f4390f8d30c2dd92ec9f095b65e2b9ae9b0a925a5258e241c9f1e910f734318")
        Main.check("sha512 abc", Hash.sha512Hex("abc") == "ddaf35a193617abacc417349ae20413112e6fa4e89a97ea20a9eeee64b55d39a2192992a274fc1a836ba3c23a3feebbd454d4423643ce80e2a9ac94fa54ca49f")
        Main.check("sha512 empty", Hash.sha512Hex("") == "cf83e1357eefb8bdf1542850d66d8007d620e4050b5715dc83f4a921d36ce9ce47d0d13c5d85f2b0ff8318d2877eec2f63b931bd47417a81a538327af927da3e")
        Main.check("crc32", Hash.crc32(Text.bytes("123456789")) == 0xCBF43926 and Hash.crc32(Text.bytes("")) == 0)
        Main.check("hmac", Hex.encode(Hash.hmacSha256(Text.bytes("key"), Text.bytes("The quick brown fox jumps over the lazy dog"))) == "f7bc83f430538424b13298e6aa6fb143ef4d59a14946175997479dbc2d1a3cd8")
        long_key = new List[int]()
        for i in range(100):
            long_key.add(170)
        Main.check("hmac long key", Hex.encode(Hash.hmacSha256(long_key, Text.bytes("Test Using Larger Than Block-Size Key - Hash Key First"))) == "ae7784e245977b78cd7a9414f496ddbba31ea448bdd61e91c37f002c72f52442")
        Main.check("pbkdf2 1", Hex.encode(Hash.pbkdf2("password", Text.bytes("salt"), 1, 32)) == "120fb6cffcf8b32c43e7225256c4f837a86548c92ccc35480805987cb70be17b")
        Main.check("pbkdf2 2", Hex.encode(Hash.pbkdf2("password", Text.bytes("salt"), 2, 32)) == "ae4d0c95af6b46d32d0adff928f06dd02a303f8ef3c251dfd6e2d85a95474c43")
        Main.check("pbkdf2 long output", Hash.pbkdf2("password", Text.bytes("salt"), 1, 40).size() == 40)

        long_key = null
        if heap_live() - base == 0:
            print("ok   no leaks")
        else:
            print("LEAK", heap_live() - base)
