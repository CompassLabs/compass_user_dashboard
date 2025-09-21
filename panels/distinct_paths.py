import os
from datetime import datetime, timedelta

import polars as pl
from dotenv import load_dotenv
from logfire.query_client import AsyncLogfireQueryClient
from PIL.ImageChops import offset

load_dotenv()


async def get_distinct_paths(
    min_datetime: datetime, max_datetime: datetime, user_email: str
):
    query = f"""
SELECT
    start_timestamp,
    url_path,
    duration
FROM
  records
WHERE
  (
    span_name LIKE 'GET%' OR span_name LIKE 'POST%'
  )
  AND attributes ->> 'http.request.header.x_user_email' ->> 0 = '{user_email}'
ORDER BY url_path
    """

    async with AsyncLogfireQueryClient(
        read_token=os.environ.get("LOGFIRE_API_KEY", "")
    ) as client:
        df_from_arrow = pl.from_arrow(
            await client.query_arrow(
                sql=query,
                min_timestamp=min_datetime,
                max_timestamp=max_datetime,
                limit=10000,
            )
        )
        df = df_from_arrow.to_pandas()
        df["duration"] *= 1000
        return df


if __name__ == "__main__":
    import asyncio

    result = asyncio.run(
        get_distinct_paths(
            datetime.today() - timedelta(days=31),
            datetime.now(),
            "zhimao@cybertinolab.com",
        )
    )
    print(result)
