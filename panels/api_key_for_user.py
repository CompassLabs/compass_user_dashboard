import os

import polars as pl
from dotenv import load_dotenv
from logfire.query_client import AsyncLogfireQueryClient

load_dotenv()


async def get_api_key_for_user(user_email: str):
    query = f"""
SELECT
distinct attributes ->> 'http.request.header.x_api_key'->>0 as api_key
from records
where attributes ->> 'http.request.header.x_user_email' ->> 0 = '{user_email}'
and attributes ->> 'http.request.header.x_api_key' is not null
"""

    async with AsyncLogfireQueryClient(
        read_token=os.environ.get("LOGFIRE_API_KEY", "")
    ) as client:
        df_from_arrow = pl.from_arrow(await client.query_arrow(sql=query))
        df = df_from_arrow.to_pandas()
        return df["api_key"].values[0]


if __name__ == "__main__":
    import asyncio

    result = asyncio.run(get_api_key_for_user("aidar@compasslabs.ai"))
    print(result)
