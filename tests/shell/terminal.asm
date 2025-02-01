UPDATE_CURSOR:
    MOV32 [0xB000], [CURSOR_X]
    MOV32 [0xB004], [CURSOR_Y]
    RET
PUT_CHAR:
    ; X = G1
    ; Y = G2
    ; CH = G3
    PUSH64 G4
    MOV64 G4, 0
    ; Y*WIDTH+X
    MOV32 G4, G2
    MUL32 G4, 80
    ADD32 G4, G1
    MOV8 [0xB010+G4], G3
    POP64 G4
    RET
PRINT:
    ; STR = G0
PRINT_LOOP:
    CMP8 [G0], 0
    JE PRINT_EXIT
    CMP8 [G0], 10
    JE PRINT_NL
    MOV32 G1, [CURSOR_X]
    MOV32 G2, [CURSOR_Y]
    MOV8 G3, [G0]
    CALL PUT_CHAR
    ADD32 [CURSOR_X], 1
    CALL UPDATE_CURSOR
    ADD64 G0, 1
    JMP PRINT_LOOP
PRINT_NL:
    ADD32 [CURSOR_Y], 1
    MOV32 [CURSOR_X], 0
    CALL UPDATE_CURSOR
    ADD64 G0, 1
    JMP PRINT_LOOP
PRINT_EXIT:
    RET
CURSOR_X: D32 0
CURSOR_Y: D32 0