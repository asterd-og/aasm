all:
	python3 src/main.py tests/main.asm prg.bin
	cp prg.bin ../astro64
	../astro64/out/astro64 ../astro64/prg.bin
