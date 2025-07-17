import polars as pl
from logfire.query_client import AsyncLogfireQueryClient


async def get_reponse_codes_table(min_datetime, max_datetime):
    query = """
SELECT
  cast(http_response_status_code as varchar) as response_code,
  COUNT(*) AS num_seen
FROM
  records
WHERE
  (
    span_name LIKE 'GET%' OR span_name LIKE 'POST%'
  )
  AND attributes ->> 'http.request.header.x_user_email' ->> 0 = 'aidar@compasslabs.ai'
GROUP BY
  http_response_status_code
ORDER BY
  num_seen DESC;
    """

    async with AsyncLogfireQueryClient(
        read_token="pylf_v1_eu_tRNktBRvGfzSbJnQ5Z5rywXPfbR18bTP9kLxLKZ2F2pC"
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
