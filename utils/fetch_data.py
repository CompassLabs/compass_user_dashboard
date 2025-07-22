import os
from datetime import datetime, timedelta

import polars as pl
from dotenv import load_dotenv
from logfire.query_client import AsyncLogfireQueryClient

load_dotenv()

PAGE_SIZE = 10000
LOGFIRE_API_KEY = os.environ["LOGFIRE_API_KEY"]      # fail fast if missing


async def fetch_records_between(
    min_timestamp: datetime,
    max_timestamp: datetime
) -> "pd.DataFrame":
    """Fetch every `request_data` row between two timestamps."""
    offset = 0
    pages = []
    client = AsyncLogfireQueryClient(read_token=LOGFIRE_API_KEY)
    while True:
        sql = f"""
        SELECT *
        FROM   records
        WHERE  span_name = 'request_data'
        ORDER  BY CAST(created_at AS TIMESTAMP) DESC
        LIMIT  {PAGE_SIZE} OFFSET {offset}
        """

        page = pl.from_arrow(
            await client.query_arrow(sql=sql, min_timestamp=min_timestamp, max_timestamp=max_timestamp, limit=10000)
        )
        if page.is_empty():
            break
        pages.append(page)

        if page.height < PAGE_SIZE:  # last page reached
            break
        offset += PAGE_SIZE  # next slice
    df = pl.concat(pages).to_pandas()
    return df


if __name__ == "__main__":
    import asyncio

    result = asyncio.run(
        fetch_records_between(
            min_timestamp = datetime.today() - timedelta(days=14),
            max_timestamp = datetime.now(),
        )
    )
    print(result)