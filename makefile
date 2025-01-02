all:
	python3 src/aasm.py tests/main.asm prg.bin
	python3 src/ald.py prg.bin out.bin
	cp out.bin ../astro64/prg.bin
	$(MAKE) -C ../astro64
