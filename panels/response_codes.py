import polars as pl
from logfire.query_client import AsyncLogfireQueryClient
from dotenv import load_dotenv
import os
from datetime import datetime

load_dotenv()


async def get_reponse_codes_table(
    min_datetime: datetime, max_datetime: datetime, user_email: str
):
    query = f"""
SELECT
  cast(http_response_status_code as varchar) as response_code,
  COUNT(*) AS num_seen
FROM
  records
WHERE
  (
    span_name LIKE 'GET%' OR span_name LIKE 'POST%'
  )
  AND attributes ->> 'http.request.header.x_user_email' ->> 0 = '{user_email}'
GROUP BY
  http_response_status_code
ORDER BY
  num_seen DESC;
    """

    async with AsyncLogfireQueryClient(
        read_token=os.environ.get("LOGFIRE_API_KEY")
    ) as client:
        df_from_arrow = pl.from_arrow(
            await client.query_arrow(
                sql=query, min_timestamp=min_datetime, max_timestamp=max_datetime
            )
        )
        return df_from_arrow


if __name__ == "__main__":
    import asyncio

    asyncio.run(get_reponse_codes_table())
