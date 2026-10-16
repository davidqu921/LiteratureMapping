# Example inputs

`sample_lit_map.csv` is the original 17-record education literature map. `../configs/sample.json` assigns its attributes to Population, Evaluation, and Intervention. It is a runnable format example, not sycophancy evidence.

From the repository root:

```sh
python -m scripts.csv_to_latex --out build/sample
```

`Literature Mapping Template.xlsx` is the earlier illustrative spreadsheet template. The actual project coding workbook is in `../data/`. The generator reads CSV exports; it does not consume this Excel template directly. See [the data format](../docs/DATA_FORMAT.md) before adapting it.
