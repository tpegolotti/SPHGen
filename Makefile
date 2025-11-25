FLAGS=-O3 -march=native -Intl/include -lntl --std=c++20 -lgmp -mtune=native -frename-registers -fschedule-fusion -flive-range-shrinkage -fmodulo-sched -fmodulo-sched-allow-regmoves -fschedule-insns -fschedule-insns2 -fsched-pressure -fira-region='all' -fsched-spec-load -fprefetch-loop-arrays
TEST_FLAGS=-O0 -march=native -Intl/include -lntl --std=c++20 -lgmp -g
FACTOR=800
PI=150
THETA=3
SIMD=4
LOWER=4
UPPER=100
UNROLL=1
MADD=
KARA=
NEWC=
OPTIONS=$(MADD) $(KARA) $(NEWC)
STRIDE=1

PIs = 101 102 103 104 105 106 107 108 109 110 111 112 113 114 115 116 117 118 119 120 121 122 123 124 125 126 127 128 129 130 131 132 133 134 135 136 137 138 139 140 141 142 143 144 145 146 147 148 149 150 151 152 153 154 155 156 157 158 159 160 161 162 163 164 165 166 167 168 169 170 171 172 173 174 175 176 177 178 179 180 181 182 183 184 185 186 187 188 189 190 191 192 193 194 195 196 197 198 199 200 201 202 203 204 205 206 207 208 209 210 211 212 213 214 215 216 217 218 219 220 221 222 223 224 225 226 227 228 229 230 231 232 233 234 235 236 237 238 239 240 241 242 243 244 245 246 247 248 249 250 251 252 253 254 255 256 257 258 259 260 261 262 263 264 265 266 267 268 269 270 271 272 273 274 275 276 277 278 279 280 281 282 283 284 285 286 287 288 289 290 291 292 293 294 295 296 297 298 299 300 301 302 303 304 305 306 307 308 309 310 311 312 313 314 315 316 317 318 319 320 321 322 323 324 325 326 327 328 329 330 331 332 333 334 335 336 337 338 339 340 341 342 343 344 345 346 347 348 349 350 351 352 353 354 355 356 357 358 359 360 361 362 363 364 365 366 367 368 369 370 371 372 373 374 375 376 377 378 379 380 381 382 383 384 385 386 387 388 389 390 391 392 393 394 395 396 397 398 399 400
THETAs = 69 33 97 17 13 117 1 59 31 21 37 75 133 11 67 3 279 5 69 119 73 3 67 59 9 137 1 159 25 5 69 347 99 45 45 113 13 105 187 27 9 111 69 83 151 153 145 167 31 3 195 17 69 243 31 143 19 15 91 47 159 101 55 63 25 5 135 257 643 143 19 95 55 3 229 233 339 41 49 47 165 161 147 33 303 371 85 125 25 11 19 237 31 33 135 15 75 17 49 75 55 183 159 167 81 5 91 299 33 47 175 23 3 185 157 377 61 33 121 77 3 117 235 63 49 5 405 93 91 27 165 567 3 83 15 209 181 161 87 467 39 63 9 189 163 107 81 237 75 207 9 129 273 245 19 189 93 87 361 149 223 71 747 275 49 3 265 77 241 53 169 237 205 305 129 89 103 93 69 47 139 83 45 173 9 165 115 167 493 47 19 167 601 35 171 285 123 341 69 153 265 267 121 75 103 503 99 159 493 77 45 203 139 113 465 57 33 165 795 197 9 11 141 23 399 101 595 155 139 255 61 707 483 243 321 3 75 15 147 293 229 65 199 119 475 45 211 117 285 113 61 657 139 153 49 173 243 671 411 719 369 605 75 923 169 167 487 315 25 495 741 177 333 65 679 57 259 417 19 65 313 105 31 317 265 231 615 45 21 137 105 107 93 377 531 605 81 131 91 593

bin:
	mkdir -p bin

generate: src/main.cpp
	python3 gen.py -p $(PI) -t $(THETA) -s $(SIMD) -u $(UNROLL) -pr $(OPTIONS)

generate_jasmin: src/main.cpp
	python3 gen.py -p $(PI) -t $(THETA) -s $(SIMD) -u $(UNROLL) -pr $(OPTIONS) -j
	jasminc -checksafety src/library.jazz
	jasminc -pasm src/library.jazz > src/library.s

verify: bin generate src/main.cpp
	python3 src/verify.py

main: bin generate src/main.cpp
	g++ src/main.cpp -o bin/main $(FLAGS);
	python3 src/verify.py;\

asm: bin generate src/main.cpp
	g++ src/main.cpp -o bin/main.s -S $(FLAGS)

test: bin generate src/main.cpp
	@g++ src/main.cpp -o bin/test $(TEST_FLAGS) -DTEST; \
	python3 src/verify.py;\
	for number in `seq $(LOWER) $(UPPER)`; do \
        ./bin/test $$number; \
    done \

test_jasmin: bin generate_jasmin src/main.cpp src/library.s
	@g++ src/main.cpp src/library.s -o bin/test_jasmin $(TEST_FLAGS) -DTEST; \
	python3 src/verify.py;\
	for number in `seq $(LOWER) $(UPPER)`; do \
        ./bin/test_jasmin $$number; \
    done \

plot: bin src/main.cpp
	@pis=`echo $(PIs)`; \
	thetas=`echo $(THETAs)`; \
	length=`echo $$pis | wc -w`; \
	for i in `seq 1 $(STRIDE) $$length`; do \
		pi=`echo $$pis | cut -d ' ' -f $$i`; \
		theta=`echo $$thetas | cut -d ' ' -f $$i`; \
		python3 gen.py -p $$pi -t $$theta -s $(SIMD) -u $(UNROLL) $(OPTIONS); \
		g++ src/main.cpp -o bin/plot $(FLAGS) -DPLOT; \
		./bin/plot $$(( 1600 + $(SIMD) )); \
	done
	
bench_hacl:
# 	export LD_LIBRARY_PATH=$(shell pwd)/others/hacl-star/dist/gcc-compatible:$LD_LIBRARY_PATH
	@echo "bytes,cycles,multiplier,num_runs"
	@for len in $(shell seq 128 512 25600); do \
		g++ others/benchmark_hacl.cpp -o bin/bench_hacl \
		-Iothers/hacl-star/dist/gcc-compatible \
		-Lothers/hacl-star/dist/gcc-compatible \
		-Iothers/hacl-star/dist/karamel/include/ \
		-Iothers/hacl-star/dist/karamel/krmllib/dist/minimal/ \
		-levercrypt -O3 -march=native -DSTRING_LEN=$$len; \
		./bin/bench_hacl; \
	done

bench_openssl: ./others/benchmark_openssl.cpp
	@echo "bytes,cycles"
	@for len in $(shell seq 128 512 25600); do \
		g++ -I/home/tpegolotti/git/SPHGen/others/opensll/include -O3 -march=native \
			-o bin/bench_openssl ./others/benchmark_openssl.cpp \
			-Lothers/openssl \
			-l:libssl.a \
			-l:libcrypto.a \
			-lz -ldl -static-libgcc -DSTRING_LEN=$$len; \
		./bin/bench_openssl; \
	done

bench_one_inc: bin src/main.cpp
	@echo "bytes,cycles"
	@python3 gen.py -p $(PI) -t $(THETA) -s $(SIMD) -u $(UNROLL) $(OPTIONS); 
	@g++ src/main.cpp -o bin/bench $(FLAGS) -DBENCH_ONE;
	@for len in $(shell seq 8 32 1600); do \
		./bin/bench $$len; \
	done

clean:
	rm -f bin/*
