all:
	python3 src/aasm.py tests/firmware/main.asm fba.bin
	python3 src/aasm.py tests/kernel/main.asm kernel.bin
	cp *.bin ../astro64/
	$(MAKE) -C ../astro64
