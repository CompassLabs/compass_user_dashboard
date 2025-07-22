import os

import polars as pl
from dotenv import load_dotenv
from logfire.query_client import AsyncLogfireQueryClient

load_dotenv()


async def get_distinct_users():
    query = f"""
SELECT
    distinct attributes ->> 'http.request.header.x_user_email' ->> 0 as users
FROM
  records
WHERE
    span_name LIKE 'GET%' OR span_name LIKE 'POST%'
    """

    async with AsyncLogfireQueryClient(
        read_token=os.environ.get("LOGFIRE_API_KEY", "")
    ) as client:
        df_from_arrow = pl.from_arrow(await client.query_arrow(sql=query))
        df = df_from_arrow.to_pandas()
        return df["users"]


if __name__ == "__main__":
    import asyncio

    result = asyncio.run(get_distinct_users())
    print(result)
