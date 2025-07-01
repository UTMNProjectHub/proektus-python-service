import os
import psycopg2
from psycopg2.extras import execute_values
import uuid


class MetadataDBClient:
    def __init__(self):
        dsn = os.getenv("DB_URL")
        if not dsn:
            raise RuntimeError("Нужно задать строку подключения в DB_URL")
        self.dsn = dsn

    def save_project_metadata(self, project_id: int, metadata: dict):
        conn = psycopg2.connect(self.dsn)
        try:
            with conn:
                with conn.cursor() as cur:
                    vec = metadata["embedding"]
                    if hasattr(vec, "tolist"):
                        vec = vec.tolist()
                    vec_literal = "[" + ",".join(map(str, vec)) + "]"

                    cur.execute(
                        """
                        UPDATE projects
                           SET embedding        = %s::vector,
                               short_description = %s,
                               description       = %s,
                               annotation        = %s
                         WHERE id = %s
                        """,
                        (
                            vec_literal,
                            metadata["summary"],
                            metadata["description"],
                            metadata["annotation"],
                            project_id,
                        ),
                    )

                    links = metadata.get("repository_links", [])
                    if links:
                        first_link = links[0]
                        cur.execute(
                            "DELETE FROM project_urls WHERE project_id = %s",
                            (project_id,),
                        )
                        cur.execute(
                            """
                            INSERT INTO project_urls (project_id, repository_url)
                            VALUES (%s, %s)
                            """,
                            (project_id, first_link),
                        )

                    keywords = metadata.get("keywords", [])
                    if keywords:
                        kw_rows = [(project_id, kw) for kw in keywords]
                        execute_values(
                            cur,
                            """
                            INSERT INTO project_keys (project_id, key)
                            VALUES %s
                            ON CONFLICT (project_id, key) DO NOTHING
                            """,
                            kw_rows,
                        )

                    tags = metadata.get("tags_list", [])
                    if tags:
                        cur.execute(
                            "SELECT id, name FROM tags WHERE name = ANY (%s)",
                            (tags,),
                        )
                        found = {name: _id for _id, name in cur.fetchall()}
                        pt_rows = []
                        for t in tags:
                            tag_id = found.get(t)
                            if tag_id:
                                pt_rows.append((project_id, tag_id))
                        if pt_rows:
                            execute_values(
                                cur,
                                """
                                INSERT INTO project_tags (project_id, tag_id)
                                VALUES %s
                                ON CONFLICT (project_id, tag_id) DO NOTHING
                                """,
                                pt_rows,
                            )

        finally:
            conn.close()

    def create_random_project(self) -> int:
        random_name = f"project_{uuid.uuid4().hex[:8]}"

        conn = psycopg2.connect(self.dsn)
        try:
            with conn:
                with conn.cursor() as cur:
                    cur.execute(
                        """
                        INSERT INTO projects (title)
                        VALUES (%s)
                        RETURNING id
                        """,
                        (random_name,),
                    )
                    project_id = cur.fetchone()[0]
        finally:
            conn.close()

        return project_id
