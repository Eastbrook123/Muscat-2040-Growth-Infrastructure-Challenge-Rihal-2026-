import pandas as pd


def main() -> None:
    path = r"c:\Users\musafa\OneDrive\Desktop\rihal\MOH_health_units_data.xlsx"
    xl = pd.ExcelFile(path)
    print("sheets:", xl.sheet_names)

    for sheet in xl.sheet_names:
        df = xl.parse(sheet)
        print("\n===", sheet, "===")
        print("shape:", df.shape)
        print("columns:", list(df.columns))
        with pd.option_context("display.max_columns", 200, "display.width", 180):
            print(df.head(8).to_string(index=False))


if __name__ == "__main__":
    main()

