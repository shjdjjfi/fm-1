.PHONY: verify-cert cert-tests cert-benchmarks

EXAMPLE ?= example5
CERT_OUT ?= out/$(EXAMPLE).full.json
COMPRESSED_OUT ?= out/$(EXAMPLE).compressed.json

verify-cert:
	@if [ "$(EXAMPLE)" = "binary_search" ] || [ "$(EXAMPLE)" = "binary-search" ]; then \
		./rustydl-cert verify examples/binary-search/binary-search.key --emit-cert $(CERT_OUT); \
	elif [ -f examples/paper/$(EXAMPLE).proof ]; then \
		./rustydl-cert from-proof examples/paper/$(EXAMPLE).proof --out $(CERT_OUT); \
	else \
		./rustydl-cert verify examples/paper/$(EXAMPLE).key --emit-cert $(CERT_OUT); \
	fi
	./rustydl-cert check $(CERT_OUT)
	./rustydl-cert compress $(CERT_OUT) --out $(COMPRESSED_OUT)
	./rustydl-cert check-compressed $(COMPRESSED_OUT)

cert-tests:
	python3 -m unittest discover -s tests -p '*tests.py'

cert-benchmarks:
	./rustydl-cert benchmark --out results
