import pandas as pd


def read_data():
    df = pd.read_csv("/data_verify.csv")
    return df


def create_final_result(df):
    result_dict = dict()
    unique_exec_date = df['execution_date'].unique()
    for unique_date in unique_exec_date:
        rows = df[df['execution_date'] == unique_date]['Symbol'].to_list()
        result_dict.update({unique_date: rows})
    result = pd.DataFrame(result_dict)
    return result


def create_required_result(df):
    temp_result = list()
    temp_df = [x for _, x in df.groupby(['execution_date', 'historical_date'])]
    for df_temp in temp_df:
        df1 = df_temp.sort_values('percent_change', ascending=False).groupby(
            ['execution_date', 'historical_date']).head(20)
        temp_result.append(df1)

    final_result = pd.concat(temp_result, ignore_index=True)
    result = create_final_result(final_result)

    return result


def main():
    df = read_data()
    result = create_required_result(df)
    result.to_csv("sorted_data.csv", index=False)
    return result


if __name__ == '__main__':
    main()
