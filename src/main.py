import sys
from enum import Enum

TokenType = Enum("TokenType", "Eof Add Sub Mul Div Mov Jmp Rel Org Id Reg Num Comma LBrac RBrac Colon Plus Minus")

class OpCodes(Enum):
    Nop = 0b000000
    Add = 0b000001
    Sub = 0b000010
    Mul = 0b000011
    Div = 0b000100
    Mov = 0b000101
    Jmp = 0b000110

def NewToken(Type, Value, Position):
    return (Type, Value, Position)

Keywords = {}
SingleChars = {',': TokenType.Comma, '[': TokenType.LBrac, ']': TokenType.RBrac,
               '+': TokenType.Plus, '-': TokenType.Minus, ':': TokenType.Colon}
def CreateKeywords():
    PrefixKw = {"add": TokenType.Add, "sub": TokenType.Sub,
                "mul": TokenType.Mul, "div": TokenType.Div,
                "mov": TokenType.Mov}
    NoPrefixKw = {"org": TokenType.Org,
                  "jmp": TokenType.Jmp,
                  "jc": TokenType.Jmp,
                  "jz": TokenType.Jmp,
                  "rel": TokenType.Rel}
    for Keyword in PrefixKw:
        for i in ["8", "16", "32", "64"]:
            Keywords[f"{Keyword}{i}"] = PrefixKw[Keyword]
    for Keyword in NoPrefixKw:
        Keywords[Keyword] = NoPrefixKw[Keyword]
    for i in range(11):
        Keywords[f"g{i}"] = TokenType.Reg

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
        elif Input[Index] == ';':
            while Input[Index] != '\n':
                Index += 1
        elif Input[Index] in SingleChars:
            Tokens.append(NewToken(SingleChars[Input[Index]], Input[Index], (Position[0], Position[1])))
            Index += 1
            Position[1] += 1
    Tokens.append(NewToken(TokenType.Eof, "", (Position[0], Position[1])))
    return Tokens

class Parser:
    def __init__(self, Tokens):
        self.Tokens = Tokens
        self.Index = -1
        self.Sizes = {"8": 0, "16": 1, "32": 2, "64": 3}
        self.Program = []
        self.Address = 0
        self.Labels = {}
        self.QueuedLabels = {}

    def Error(self, Message):
        print(f"Error at {self.Tokens[self.Index][2][0]}:{self.Tokens[self.Index][2][1]}: {Message}")
        exit(1)

    def Eat(self, Type):
        self.Index += 1
        if self.Tokens[self.Index][0] != Type:
            self.Error(f"Unexpected token.")

    def Consume(self):
        self.Index += 1
        return self.Tokens[self.Index]

    def Peek(self):
        return self.Tokens[self.Index + 1]

    def GetRegister(self, Register):
        return int(Register[1:])

    def GetInt(self, Int):
        if len(Int) > 2 and Int[1].lower() == 'x':
            return int(Int, 16)
        return int(Int)

    def Write8(self, Value):
        self.Program.append(Value & 0xFF)

    def Write16(self, Value):
        self.Program.extend(Value.to_bytes(2, byteorder="little"))

    def Write32(self, Value):
        self.Program.extend(Value.to_bytes(4, byteorder="little"))

    def Write64(self, Value):
        self.Program.extend(Value.to_bytes(8, byteorder="little"))

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

    def HandleOpInst(self, Token, OpCode):
        InstSize = self.Sizes[Token[1][3:6]]
        InstDstTok = self.Consume()
        InstDst = 0
        InstFlags = 0
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
            elif InstAddrTok[0] == TokenType.Num:
                InstDst = 2
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
        self.Eat(TokenType.Comma)
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
            elif InstAddrTok[0] == TokenType.Num:
                InstSrc = 3
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
        elif InstSrcTok[0] == TokenType.Num:
            InstSrc = 2
            Src = self.GetInt(InstSrcTok[1])

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
        elif Token[1] == "jz":
            CondFlags |= 0b00000100
        if self.Peek()[0] == TokenType.Rel:
            self.Consume()
            CondFlags |= 0b00000001
        LabelTok = self.Consume()
        Addr = 0
        if LabelTok[0] == TokenType.Id:
            Label = LabelTok[1]
            if Label not in self.Labels:
                Addr = 0
                self.QueuedLabels[len(self.Program) + 3] = Label # Queue label
        Instruction = self.Instruction(3, OpCodes.Jmp, 0, 0, 0)
        self.Write16(Instruction)
        self.Write8(CondFlags)
        self.Write64(Addr)

    def ParsePostamble(self):
        for Key in self.QueuedLabels:
            Label = self.QueuedLabels[Key]
            if Label not in self.Labels:
                print(f"Error: Undefined label {Label}.")
                exit(1)
            self.Program[Key] = self.Labels[Label]

    def Parse(self):
        Token = self.Tokens[0]
        while Token[0] != TokenType.Eof:
            Token = self.Consume()
            if Token[0] == TokenType.Add:
                self.HandleOpInst(Token, OpCodes.Add)
            elif Token[0] == TokenType.Sub:
                self.HandleOpInst(Token, OpCodes.Sub)
            elif Token[0] == TokenType.Mul:
                self.HandleOpInst(Token, OpCodes.Mul)
            elif Token[0] == TokenType.Div:
                self.HandleOpInst(Token, OpCodes.Div)
            elif Token[0] == TokenType.Mov:
                self.HandleOpInst(Token, OpCodes.Mov)
            elif Token[0] == TokenType.Jmp:
                self.HandleJmp(Token)
            elif Token[0] == TokenType.Org:
                self.HandleOrg(Token)
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
    print(LocalParser.Program)
    with open(sys.argv[2], "wb") as Out:
        Out.write(bytearray(LocalParser.Program))
