.PHONY: demo test lint format clean

demo:
	uv run sv-ref generate tests/samples/basic_types.sv tests/samples/nested.sv -o demo_output/
	@echo "Demo output written to demo_output/"

test:
	uv run pytest tests/ -v

lint:
	uv run ruff check sv_ref/ tests/

format:
	uv run ruff format sv_ref/ tests/

clean:
	rm -rf demo_output/
