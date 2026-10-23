.PHONY: verify figures test lint experiments experiments-all notebook data compare all

verify:        ## reconcile the paper's numbers and tables with the result files (45 checks)
	python scripts/verify_results.py results experiments/results

figures:       ## regenerate Figures 2 and 3 from results/ (vector PDF and 600 dpi PNG)
	python figures/build_figures.py results

test:          ## unit tests, including exact checks of the theorems
	pytest -q

lint:          ## static analysis
	python -m pyflakes src/certdisc scripts experiments figures/build_figures.py

data:          ## fetch the checksummed public inputs for experiments/
	bash experiments/fetch_data.sh

experiments:   ## re-run the independent pipeline and the revision experiments (five earlier models)
	cd experiments && for s in exp0_census_reproduction exp1_oracle_budgets exp2_benchmark_transfer exp3_cost_proxy exp4_shared_budget exp5_reproduce_e1_e3; do python $$s.py || exit 1; done

compare:       ## compare re-executed experiment outputs with the committed files (numerical, platform-independent)
	python scripts/compare_results.py experiments/results

experiments-all: ## the fifteen-model re-execution (needs data/frontier/, or WBM_DATA_SOURCE=url with figshare access)
	cd experiments && MODELS=all python exp5_reproduce_e1_e3.py && MODELS=all python exp4_shared_budget.py

notebook:      ## execute the analysis notebook headlessly; outputs go to results_rerun/ (results/ is left untouched)
	python -c "import nbformat; from nbclient import NotebookClient; nb = nbformat.read('notebooks/analysis.ipynb', as_version=4); NotebookClient(nb, timeout=3600, kernel_name='python3').execute(); print('notebook executed; outputs in results_rerun/')"

all: lint test verify figures
