main:
    MOV8 G1, 1
    MOV8 G2, 1
    SUB8 G1, 1                   ; Se FLAGS for 2, então deu 0
    ;; Logo, G1 e G2 são iguais.
    JZ .main                    ; Caso forem iguais, pule para .main
    MOV8 G2, 0x42           ; Não deve rodar
    ;; Logo, G2 deve ser 0x69 e não 0x42
    JMP .exit
.main:
    MOV8 G2, 0x69
.exit:
