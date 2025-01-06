import sys
from enum import Enum

TokenType = Enum("TokenType", "Eof Add Sub Mul Div Mov Jmp Rel Push Pop Call Ret And Or Xor Not Shl Shr Sei Sdi Int Cmp Org Id Str Define Res Reg Num Comma LBrac RBrac Colon Plus Minus PreProc")

class OpCodes(Enum):
    Nop =  0b000000
    Add =  0b000001
    Sub =  0b000010
    Mul =  0b000011
    Div =  0b000100
    Mov =  0b000101
    Jmp =  0b000110
    Push = 0b000111
    Pop =  0b001000
    Call = 0b001001
    Ret =  0b001010
    And =  0b001011
    Or =   0b001100
    Xor =  0b001101
    Not =  0b001110
    Shl =  0b001111
    Shr =  0b010000
    Sei =  0b010001
    Sdi =  0b010010
    Int =  0b010011
    Cmp =  0b010100

def NewToken(Type, Value, Position):
    return (Type, Value, Position)

Keywords = {}
SingleChars = {',': TokenType.Comma, '[': TokenType.LBrac, ']': TokenType.RBrac,
               '+': TokenType.Plus, '-': TokenType.Minus, ':': TokenType.Colon}
Macros = {}
def CreateKeywords():
    PrefixKw = {"add": TokenType.Add, "sub": TokenType.Sub,
                "mul": TokenType.Mul, "div": TokenType.Div,
                "mov": TokenType.Mov, "push": TokenType.Push,
                "pop": TokenType.Pop, "d": TokenType.Define,
                "and": TokenType.And, "or": TokenType.Or,
                "xor": TokenType.Xor, "not": TokenType.Not,
                "shl": TokenType.Shl, "shr": TokenType.Shr,
                "res": TokenType.Res, "cmp": TokenType.Cmp}
    NoPrefixKw = {"org": TokenType.Org,
                  "jmp": TokenType.Jmp,
                  "jc": TokenType.Jmp,
                  "jz": TokenType.Jmp,
                  "je": TokenType.Jmp,
                  "jg": TokenType.Jmp,
                  "jge": TokenType.Jmp,
                  "jl": TokenType.Jmp,
                  "jle": TokenType.Jmp,
                  "rel": TokenType.Rel,
                  "call": TokenType.Call,
                  "ret": TokenType.Ret,
                  "sei": TokenType.Sei,
                  "sdi": TokenType.Sdi,
                  "int": TokenType.Int}
    for Keyword in PrefixKw:
        for i in ["8", "16", "32", "64"]:
            Keywords[f"{Keyword}{i}"] = PrefixKw[Keyword]
    for Keyword in NoPrefixKw:
        Keywords[Keyword] = NoPrefixKw[Keyword]

    # Registers
    for i in range(11):
        Keywords[f"g{i}"] = TokenType.Reg
    Keywords["sp"] = TokenType.Reg
    Keywords["fp"] = TokenType.Reg
    Keywords["ip"] = TokenType.Reg
    Keywords["flags"] = TokenType.Reg
    Keywords["pgtbl"] = TokenType.Reg
    Keywords["ivtbl"] = TokenType.Reg
    Keywords["err"] = TokenType.Reg

def Tokenize(Input):
    Tokens = []
    Index = 0
    Position = [1, 1] # Row, Column
    while Index < len(Input):
        if Input[Index] in " \t\n\r":
            if Input[Index] in "\n\r":
                Position[0] += 1
                Position[1] = 1
            else:
                Position[1] += 1
            Index += 1
        elif ('a' <= Input[Index] <= 'z'
              or 'A' <= Input[Index] <= 'Z'
              or Input[Index] == '_' or Input[Index] == '.'):
            Id = ""
            while ('a' <= Input[Index] <= 'z'
                   or 'A' <= Input[Index] <= 'Z'
                   or '0' <= Input[Index] <= '9'
                   or Input[Index] == '_' or Input[Index] == '.'):
                Id += Input[Index]
                Index += 1
            Type = TokenType.Id
            if Id.lower() in Keywords:
                Id = Id.lower()
                Type = Keywords[Id]
            Tokens.append(NewToken(Type, Id, (Position[0], Position[1])))
            Position[1] += len(Id)
        elif '0' <= Input[Index] <= '9':
            Hex = False
            Num = ""
            if Input[Index + 1].lower() == 'x':
                Hex = True
                Index += 2
                Num += "0x"
            while ('a' <= Input[Index] <= 'f'
                   or 'A' <= Input[Index] <= 'F'
                   or '0' <= Input[Index] <= '9'):
                Num += Input[Index]
                Index += 1
            Tokens.append(NewToken(TokenType.Num, Num, (Position[0], Position[1])))
            Position[1] += len(Num)
        elif Input[Index] == '"':
            Str = ""
            Index += 1
            Position[1] += 1
            while Input[Index] != '"':
                if Input[Index] in '\n\r':
                    print(f"Unexpected new line at string {Position[0]}:{Position[1]}")
                    exit(1)
                Str += Input[Index]
                Position[1] += 1
                Index += 1
            Index += 1
            Position[1] += 1
            Tokens.append(NewToken(TokenType.Str, Str, (Position[0], Position[1])))
        elif Input[Index] == ';':
            while Input[Index] != '\n':
                Index += 1
        elif Input[Index] == '%':
            Index += 1
            Position[1] += 1
            Id = ""
            while ('a' <= Input[Index] <= 'z'
                   or 'A' <= Input[Index] <= 'Z'
                   or '0' <= Input[Index] <= '9'
                   or Input[Index] == '_' or Input[Index] == '.'):
                Id += Input[Index]
                Index += 1
            Tokens.append(NewToken(TokenType.PreProc, Id.lower(), (Position[0], Position[1] - 1)))
            Position[1] += len(Num)
        elif Input[Index] in SingleChars:
            Tokens.append(NewToken(SingleChars[Input[Index]], Input[Index], (Position[0], Position[1])))
            Index += 1
            Position[1] += 1
        else:
            print(f"Unexpected token at {Position[0]}:{Position[1]}")
            exit(1)
    Tokens.append(NewToken(TokenType.Eof, "", (Position[0], Position[1])))
    return Tokens

class Parser:
    def __init__(self, Tokens):
        self.Tokens = Tokens
        self.Index = -1
        self.Sizes = {"8": 0, "16": 1, "32": 2, "64": 3}
        self.Registers = {"sp": 11, "fp": 12, "ip": 13, "flags": 14, "pgtbl": 15, "ivtbl": 16}
        for i in range(11):
            self.Registers[f"g{i}"] = i
        self.Program = []
        self.Address = 0
        self.Labels = {}

    def Error(self, Message):
        print(f"Error at {self.Tokens[self.Index][2][0]}:{self.Tokens[self.Index][2][1]}: {Message}")
        exit(1)

    def Eat(self, Type):
        self.Index += 1
        if self.Tokens[self.Index][0] != Type:
            self.Error(f"Unexpected token.")
        return self.Tokens[self.Index]

    def Consume(self):
        self.Index += 1
        return self.Tokens[self.Index]

    def Peek(self):
        return self.Tokens[self.Index + 1]

    def GetRegister(self, Register):
        return self.Registers[Register]

    def GetInt(self, Int):
        if len(Int) > 2 and Int[1].lower() == 'x':
            return int(Int, 16)
        return int(Int)

    def Write8(self, Value):
        if isinstance(Value, int):
            self.Program.append(Value & 0xFF)
        else:
            self.Program.extend([Value, 1])

    def Write16(self, Value):
        if isinstance(Value, int):
            self.Program.extend(Value.to_bytes(2, byteorder="little"))
        else:
            self.Program.extend([Value, 2])

    def Write32(self, Value):
        if isinstance(Value, int):
            self.Program.extend(Value.to_bytes(4, byteorder="little"))
        else:
            self.Program.extend([Value, 4, 0, 0])

    def Write64(self, Value):
        if isinstance(Value, int):
            self.Program.extend(Value.to_bytes(8, byteorder="little"))
        else:
            self.Program.extend([Value, 8, 0, 0, 0, 0, 0, 0])

    def Write(self, Value, Size):
        if Size == 0:
            self.Write8(Value)
        elif Size == 1:
            self.Write16(Value)
        elif Size == 2:
            self.Write32(Value)
        else:
            self.Write64(Value)

    def Instruction(self, Size, OpCode, Src, Dst, Flags):
        Instruction = Size << 14
        Instruction |= OpCode.value << 8
        Instruction |= Src << 6
        Instruction |= Dst << 4
        Instruction |= Flags
        return Instruction

    def HandleDst(self, InstFlags):
        InstDstTok = self.Consume()
        InstDst = 0
        Dst = 0
        DstOff = 0
        if InstDstTok[0] == TokenType.Reg:
            InstDst = 0
            Dst = self.GetRegister(InstDstTok[1])
        elif InstDstTok[0] == TokenType.LBrac:
            InstAddrTok = self.Consume()
            if InstAddrTok[0] == TokenType.Reg:
                InstDst = 1
                Dst = self.GetRegister(InstAddrTok[1])
            elif InstAddrTok[0] == TokenType.Num or InstAddrTok[0] == TokenType.Id:
                InstDst = 2
                if InstAddrTok[0] == TokenType.Id:
                    Dst = InstAddrTok[1]
                else:
                    Dst = self.GetInt(InstAddrTok[1])
            else:
                self.Error("Invalid addressing.")
            InstNextTok = self.Consume()
            if InstNextTok[0] == TokenType.Plus:
                InstFlags |= 0b0010
                InstNextTok = self.Consume()
                if InstNextTok[0] == TokenType.Reg:
                    InstFlags |= 0b1000
                    DstOff = self.GetRegister(InstNextTok[1])
                elif InstNextTok[0] == TokenType.Num:
                    DstOff = self.GetInt(InstNextTok[1])
                else:
                    self.Error("Invalid offset.")
                self.Eat(TokenType.RBrac)
            else:
                if InstNextTok[0] != TokenType.RBrac:
                    self.Error("Unexpected token.")
        else:
            self.Error("Unexpected destination.")
        return (InstDst, Dst, DstOff, InstFlags)

    def HandleSrc(self, InstFlags):
        InstSrcTok = self.Consume()
        InstSrc = 0
        Src = 0
        SrcOff = 0
        if InstSrcTok[0] == TokenType.Reg:
            InstSrc = 0
            Src = self.GetRegister(InstSrcTok[1])
        elif InstSrcTok[0] == TokenType.LBrac:
            InstAddrTok = self.Consume()
            if InstAddrTok[0] == TokenType.Reg:
                InstSrc = 1
                Src = self.GetRegister(InstAddrTok[1])
            elif InstAddrTok[0] == TokenType.Num or InstAddrTok[0] == TokenType.Id:
                InstSrc = 3
                if InstAddrTok[0] == TokenType.Id:
                    Src = InstAddrTok[1]
                else:
                    Src = self.GetInt(InstAddrTok[1])
            else:
                self.Error("Invalid addressing")
            InstNextTok = self.Consume()
            if InstNextTok[0] == TokenType.Plus:
                InstFlags |= 0b0001
                InstNextTok = self.Consume()
                if InstNextTok[0] == TokenType.Reg:
                    InstFlags |= 0b0100
                    SrcOff = self.GetRegister(InstNextTok[1])
                elif InstNextTok[0] == TokenType.Num:
                    SrcOff = self.GetInt(InstNextTok[1])
                else:
                    self.Error("Invalid offset.")
                self.Eat(TokenType.RBrac)
            else:
                if InstNextTok[0] != TokenType.RBrac:
                    self.Error("Unexpected token.")
        elif InstSrcTok[0] == TokenType.Num or InstSrcTok[0] == TokenType.Id:
            InstSrc = 2
            if InstSrcTok[0] == TokenType.Id:
                Src = InstSrcTok[1]
            else:
                Src = self.GetInt(InstSrcTok[1])
        return (InstSrc, Src, SrcOff, InstFlags)

    def HandleOpInst(self, Token, OpCode, TwoLetterInst):
        InstSize = self.Sizes[Token[1][(2 if TwoLetterInst else 3):5]]
        InstFlags = 0
        InstDst, Dst, DstOff, InstFlags = self.HandleDst(InstFlags)
        self.Eat(TokenType.Comma)
        InstSrc, Src, SrcOff, InstFlags = self.HandleSrc(InstFlags)

        Instruction = self.Instruction(InstSize, OpCode, InstSrc, InstDst, InstFlags)
        self.Write16(Instruction)

        if InstFlags & 0b0001:
            if InstFlags & 0b0100:
                self.Write8(SrcOff) # Reg src off
            else:
                self.Write64(SrcOff)
        if InstSrc == 0 or InstSrc == 1:
            self.Write8(Src)
        elif InstSrc == 2:
            self.Write(Src, InstSize)
        else:
            self.Write64(Src)

        if InstFlags & 0b0010:
            if InstFlags & 0b1000:
                self.Write8(DstOff) # Reg dst off
            else:
                self.Write64(DstOff)
        if InstDst == 0 or InstDst == 1:
            self.Write8(Dst)
        else:
            self.Write64(Dst)

    def HandlePush(self, Token):
        InstSize = self.Sizes[Token[1][4:7]]
        InstFlags = 0
        InstSrc, Src, SrcOff, InstFlags = self.HandleSrc(InstFlags)

        Instruction = self.Instruction(InstSize, OpCodes.Push, InstSrc, 0, InstFlags)
        self.Write16(Instruction)

        if InstFlags & 0b0001:
            if InstFlags & 0b0100:
                self.Write8(SrcOff) # Reg src off
            else:
                self.Write64(SrcOff)
        if InstSrc == 0 or InstSrc == 1:
            self.Write8(Src)
        elif InstSrc == 2:
            self.Write(Src, InstSize)
        else:
            self.Write64(Src)

    def HandlePop(self, Token):
        InstSize = self.Sizes[Token[1][3:6]]
        InstFlags = 0
        InstDst, Dst, DstOff, InstFlags = self.HandleDst(InstFlags)

        Instruction = self.Instruction(InstSize, OpCodes.Pop, 0, InstDst, InstFlags)
        self.Write16(Instruction)

        if InstFlags & 0b0010:
            if InstFlags & 0b1000:
                self.Write8(DstOff) # Reg dst off
            else:
                self.Write64(DstOff)
        if InstDst == 0 or InstDst == 1:
            self.Write8(Dst)
        else:
            self.Write64(Dst)

    def HandleOrg(self, Token):
        AddressTok = self.Eat(TokenType.Num)
        self.Address = self.GetInt(AddressTok[1])

    def HandleLabel(self, NameTok):
        self.Eat(TokenType.Colon)
        self.Labels[NameTok[1]] = self.Address + len(self.Program)

    def HandleJmp(self, Token):
        CondFlags = 0
        if Token[1] == "jc":
            CondFlags |= 0b00000010
        elif Token[1] == "jz" or Token[1] == "je":
            CondFlags |= 0b00000100
        elif Token[1] == "jg":
            CondFlags |= 0b00001000
        elif Token[1] == "jge":
            CondFlags |= 0b00001100
        elif Token[1] == "jl":
            CondFlags |= 0b00010000
        elif Token[1] == "jle":
            CondFlags |= 0b00010100
        if self.Peek()[0] == TokenType.Rel:
            self.Consume()
            CondFlags |= 0b00000001
        LabelTok = self.Consume()
        Addr = 0
        if LabelTok[0] == TokenType.Id:
            Label = LabelTok[1]
            if Label not in self.Labels:
                Addr = Label
            else:
                Addr = self.Labels[Label]
        else:
            Addr = self.GetInt(LabelTok[1])
        Flags = 0b0000
        Src = 2
        Instruction = self.Instruction(3, OpCodes.Jmp, Src, 0, Flags)
        self.Write16(Instruction)
        self.Write8(CondFlags)
        self.Write64(Addr)

    def HandleCall(self, Token):
        LabelTok = self.Consume()
        # TODO: Handle Reg
        if LabelTok[0] == TokenType.Id:
            Label = LabelTok[1]
            if Label not in self.Labels:
                Addr = Label
            else:
                Addr = self.Labels[Label]
        Flags = 0b0000
        Src = 2
        Instruction = self.Instruction(3, OpCodes.Call, Src, 0, Flags)
        self.Write16(Instruction)
        self.Write64(Addr)

    def HandleSimpleInst(self, Token, OpCode):
        Instruction = self.Instruction(3, OpCode, 0, 0, 0)
        self.Write16(Instruction)

    def HandleNot(self, Token):
        InstSize = self.Sizes[Token[1][3:6]]
        InstFlags = 0
        InstDst, Dst, DstOff, InstFlags = self.HandleDst(InstFlags)

        Instruction = self.Instruction(InstSize, OpCodes.Not, 0, InstDst, InstFlags)
        self.Write16(Instruction)

        if InstFlags & 0b0010:
            if InstFlags & 0b1000:
                self.Write8(DstOff) # Reg dst off
            else:
                self.Write64(DstOff)
        if InstDst == 0 or InstDst == 1:
            self.Write8(Dst)
        else:
            self.Write64(Dst)

    def HandleInt(self, Token):
        InstSrc, Src, SrcOff, InstFlags = self.HandleSrc(0)

        Instruction = self.Instruction(0, OpCodes.Int, InstSrc, 0, InstFlags)
        self.Write16(Instruction)

        if InstFlags & 0b0001:
            if InstFlags & 0b0100:
                self.Write8(SrcOff) # Reg src off
            else:
                self.Write64(SrcOff)
        if InstSrc != 3:
            self.Write8(Src)
        else:
            self.Write64(Src)
    
    def HandleDefine(self, Token):
        WSize = self.Sizes[Token[1][1:3]]
        Data = self.Consume()
        Def = 0
        if Data[0] == TokenType.Id:
            Label = Data[1]
            if Label not in self.Labels:
                Def = Label
            else:
                Def = self.Labels[Label]
        elif Data[0] == TokenType.Str:
            String = Data[1]
            for Char in String:
                self.Write(ord(Char), WSize)
            return
        else:
            Def = self.GetInt(Data[1])
        self.Write(Def, WSize)

    def HandleRes(self, Token):
        WSize = self.Sizes[Token[1][3:5]]
        Count = self.GetInt(self.Eat(TokenType.Num)[1])
        self.Program.extend([0] * ((1 << WSize) * Count))

    def HandlePreProc(self, Token):
        if Token[1] == "include":
            Name = self.Eat(TokenType.Str)
            try:
                File = open(Name[1], "r")
            except FileNotFoundError:
                self.Error(f"Couldn't find file {Name[1]}")
            Tokens = Tokenize(File.read())
            self.Tokens.pop(len(self.Tokens) - 1) # Remove EOF
            Tokens.pop(len(Tokens) - 1) # Remove Eof
            self.Tokens[self.Index + 1:self.Index + 1] = Tokens
            self.Tokens.append((TokenType.Eof, "", (0, 0)))

    def ParsePostamble(self):
        for i in range(len(self.Program)):
            if (isinstance(self.Program[i], str)):
                # Found queued label
                Size = self.Program[i + 1]
                Label = self.Program[i]
                if Label not in self.Labels:
                    print(f"Error: Undefined label {Label}.")
                    exit(1)
                self.Program[i:i + Size] = self.Labels[Label].to_bytes(Size, byteorder="little")
                if Size == 1:
                    self.Program.pop(i + 1)
                i += Size

    def Parse(self):
        Token = self.Tokens[0]
        # Emacs wont recognize the match keyword and just fucks it up. So I will use if statements instead.
        while Token[0] != TokenType.Eof:
            Token = self.Consume()
            if Token[0] == TokenType.Add:
                self.HandleOpInst(Token, OpCodes.Add, False)
            elif Token[0] == TokenType.Sub:
                self.HandleOpInst(Token, OpCodes.Sub, False)
            elif Token[0] == TokenType.Mul:
                self.HandleOpInst(Token, OpCodes.Mul, False)
            elif Token[0] == TokenType.Div:
                self.HandleOpInst(Token, OpCodes.Div, False)
            elif Token[0] == TokenType.Mov:
                self.HandleOpInst(Token, OpCodes.Mov, False)
            elif Token[0] == TokenType.Jmp:
                self.HandleJmp(Token)
            elif Token[0] == TokenType.Push:
                self.HandlePush(Token)
            elif Token[0] == TokenType.Pop:
                self.HandlePop(Token)
            elif Token[0] == TokenType.Call:
                self.HandleCall(Token)
            elif Token[0] == TokenType.Ret:
                self.HandleSimpleInst(Token, OpCodes.Ret)
            elif Token[0] == TokenType.And:
                self.HandleOpInst(Token, OpCodes.And, False)
            elif Token[0] == TokenType.Or:
                self.HandleOpInst(Token, OpCodes.Or, True)
            elif Token[0] == TokenType.Xor:
                self.HandleOpInst(Token, OpCodes.Xor, False)
            elif Token[0] == TokenType.Not:
                self.HandleNot(Token)
            elif Token[0] == TokenType.Shl:
                self.HandleOpInst(Token, OpCodes.Shl, False)
            elif Token[0] == TokenType.Shr:
                self.HandleOpInst(Token, OpCodes.Shr, False)
            elif Token[0] == TokenType.Sei:
                self.HandleSimpleInst(Token, OpCodes.Sei)
            elif Token[0] == TokenType.Sdi:
                self.HandleSimpleInst(Token, OpCodes.Sdi)
            elif Token[0] == TokenType.Int:
                self.HandleInt(Token)
            elif Token[0] == TokenType.Cmp:
                self.HandleOpInst(Token, OpCodes.Cmp, False)
            elif Token[0] == TokenType.Define:
                self.HandleDefine(Token)
            elif Token[0] == TokenType.Res:
                self.HandleRes(Token) # Reserve
            elif Token[0] == TokenType.Org:
                self.HandleOrg(Token)
            elif Token[0] == TokenType.PreProc:
                self.HandlePreProc(Token)
            elif Token[0] == TokenType.Id:
                if self.Tokens[self.Index + 1][0] == TokenType.Colon:
                    self.HandleLabel(Token)
                else:
                    self.Error("Unexpected Id.")
            else:
                if Token[0] != TokenType.Eof:
                    self.Error("Unexpected statement.")
        self.ParsePostamble()

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Expected Input File Name")
        exit(1)
    if len(sys.argv) < 3:
        print("Expected Output Name")
        exit(1)
    InputFile = open(sys.argv[1], "r")
    CreateKeywords()
    Tokens = Tokenize(InputFile.read())
    LocalParser = Parser(Tokens)
    LocalParser.Parse()
    with open(sys.argv[2], "wb") as Out:
        Out.write(bytearray(LocalParser.Program))
