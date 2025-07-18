import polars as pl
from logfire.query_client import AsyncLogfireQueryClient
from dotenv import load_dotenv
import os
from datetime import datetime, timedelta

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
        read_token=os.environ.get("LOGFIRE_API_KEY")
    ) as client:
        df_from_arrow = pl.from_arrow(
            await client.query_arrow(
                sql=query, min_timestamp=min_datetime, max_timestamp=max_datetime
            )
        )
        df = df_from_arrow.to_pandas()
        df["duration"] *= 1000
        return df


if __name__ == "__main__":
    import asyncio

    result = asyncio.run(
        get_distinct_paths(
            datetime.today() - timedelta(days=1), datetime.now(), "conor@compasslabs.ai"
        )
    )
    print(result)
