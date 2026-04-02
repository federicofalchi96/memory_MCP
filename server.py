from inspect import trace
from mcp.server.fastmcp import FastMCP
import os, json
import sqlite3
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

CURR_DIR = os.environ.get("CURR_DIR", Path.home() / "ai-memory")
DB_PATH = Path(CURR_DIR) / "memories.db"
NOTES_DIR = Path(CURR_DIR) / "notes"
KB_DIR = Path(CURR_DIR) / "kb"

# Creo cartelle se non esistono
NOTES_DIR.mkdir(parents=True, exist_ok=True)
KB_DIR.mkdir(parents=True, exist_ok=True)

mcp = FastMCP("memory-mcp")

def _get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS memories (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            created TEXT NOT NULL,
            topic TEXT NOT NULL,
            content TEXT NOT NULL,
            tags TEXT, -- json array
            importance INTEGER DEFAULT 3, -- 1=bassa, 5=alta
            source TEXT, -- da dove viene (url, file, chat)
            )
        """
    )
    conn.commit()
    return conn

# tool di salvataggio
@mcp.tool()
def save_memory(
    topic: str,
    content: str,
    tags: list[str] = None,
    importance: int = 3,
    source: str = "chat"
) ->dict:
    """
    Salva un fatto, una decisione o un'informazione importante per usi futuri.
    Usa questo tool quando l'utente dice: 'Ricordati che...', 'salva questa info', 'tieni a mente che...'
    , 'nota importante:', 'non dimenticare che...', ecc.

    Args:
        topic (str): Argomento principale della memoria.
        content (str): Contenuto della memoria.
        tags (list[str], optional): Lista di tag per categorizzare la memoria (es. ['progetto', 'decisione']).
        importance (int, optional): Livello di importanza della memoria (da 1 bassa a 5 alta).
        source (str, optional): Provenienza ('chat', 'manual', 'fomo_ai').
    
    Returns:
        dict: Confema con id e path del file .md creato
    """
    now = datetime.now()
    date_str = now.strftime("%Y-%m-%d_%H-%M-%S")
    time_str = now.strftime("%H:%M")
    
    conn = _get_db()
    cursor = conn.execute(
        """
        INSERT INTO memories (created, topic, content, tags, importance, source)
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (date_str.isoformat(), topic, content, json.dumps(tags), importance, source)
    )
    memory_id = cursor.lastrowid
    conn.commit()
    conn.close()

    # Salva come file .md (compatibile Obsidian)
    safe_topic = "".join(c if c.isalnum() or c in " -_" else "_" for c in topic)
    filename   = f"{date_str}_{safe_topic[:50]}.md"
    filepath   = NOTES_DIR / filename

    stars = "*" * importance
    tag_str = " "
    if tags:
        tag_str = " ".join(f"#{t}" for t in tags)
    
    content_md = f"""
        id: {memory_id}
        created: {date_str}
        time: {time_str}
        topic: {topic}
        tags: {json.dumps(tags)}
        importance: {importance}
        source: {source}
        ---

        # {topic}

        {stars} {tag_str}

        {content}
        ---
        Salvato il {date_str} alle ore {time_str} da Memory MCP
    """
    filepath.write_text(content_md, encoding="utf-8")

    return {
        "id": memory_id,
        "topic": topic,
        "saved_to": str(filepath),
        "message":  f"Memoria salvata con successo (importanza: {importance}/5)",
    }
# recupero memoria
@mcp.tool()
def recall_memory(
    query: str,
    tags: list[str] = [],
    min_importance: int = 1,
    limit: int = 10,
) ->list[dict]:
    """
    Cerca nelle memorie salvate per topic, keyword o tag.
    Usa questo tool quando l'utente chiede: 'cosa avevamo deciso su X?',
    'ricordami cosa so di Y', 'trova le mie note su Z'.
 
    Args:
        query:          Keyword da cercare nel topic o contenuto
        tags:           Filtra per tag specifici
        min_importance: Mostra solo memorie con importanza >= questo valore
        limit:          Numero massimo di risultati
 
    Returns:
        Lista di memorie ordinate per importanza e data
    """

    conn = _get_db()
    sql = "SELECT id, created, topic, content, tags, importance, source FROM memories WHERE importance >= ?"
    param: list = [min_importance]

    if query:
        sql += " AND (topic like ? OR content LIKE ?)"
        params += [f"%{query}", f"%{query}"]

    
    if tags:
        for tag in tags:
            sql += " AND tags LIKE ? "
            params.append(f"%{tag}%")
    
    sql += " ORDER BY importance DESC, created DESC LIMIT ?"
    params.append(limit)

    rows = conn.execute(sql, params).fetchall()
    conn.close()

    return [
        {
            "id": row[0],
            "date": row[1],
            "topic": row[2],
            "content": row[3],
            "tags": json.loads(row[4]) if row[4] else [],
            "importance": row[5],
            "source": row[6],
        }
        for row in rows
    ]


# tool 3 sommario chat e salvataggio
@mcp.tool()
def save_chat_summary(
    summary: str,
    key_decisions: list[str] = [],
    action_items: list[str] = [],
    topic: str = '',
    tags: list[str] = [],
)->dict:
    """
    Salva il sommario della conversazione corrente come file .md.
    Usa quando l'utente dice: 'salva in questa chat', 'salva questa conversazione', 'ricapitoliamo e salviamo', 'esporta il riassunto', 'salva i punti chiave'
    
    Args:
        summary:        Sommario generale della conversazione (2-5 frasi)
        key_decisions:   Lista di decisioni prese durante la chat
        action_items:   Lista di azioni da compiere
        topic:          Titolo della chat (es. 'FOMO AI — sessione 2')
        tags:           Lista di tag per categorizzare la memoria
    
    Returns:
        dict: Confema con id e path del file .md creato
    """
    now = datetime.now()
    date_str = now.strftime("%Y-%m-%d_%H-%M-%S")
    time_str = now.strftime("%H:%M")

    if not topic:
        topic = f"Chat del {date_str}"

    safe_topic = "".join(c if c.isalnum() or c in " -_" else "_" for c in topic)
    filename = f"{date_str}_{safe_topic[:60]}.md"
    filepath = NOTES_DIR / filename

    tag_str = " ".join(f"#{t}" for t in tags) if tags else ""

    decision_md = ''

    if key_decisions:
        decision_md = "## Decisioni prese \n\n"
        decision_md += "\n".join(f"- {d}" for d in key_decisions) + "\n\n"
    
    action_md = ''
    if action_items:
        action_md = "## Azioni da compiere \n\n"
        action_md += "\n".join(f"- {a}" for a in action_items) + "\n\n"

    md_content = f"""---
    date: {date_str}
    time: {time_str}
    topic: {topic}
    tags: {json.dumps(tags)}
    type: chat-summary
    ---
    
    # {topic}
    
    {tag_str}
    
    ## Sommario
    
    {summary}
    
    {decision_md}{action_md}---
    *Esportato il {date_str} alle {time_str} da Memory MCP*
    """

    filepath.write_text(md_content, encoding="utf-8")

    save_memory(
        topic = topic,
        content = summary,
        tags = tags,
        importance = 3,
        source = "chat"
    )

    return {
        "saved_to": str(filepath),
        "topic":    topic,
        "message":  f"Chat salvata in {filepath}",
    }

#mcp che recupera le note salvate
@mcp.tool()
def list_memories(
    limit:int=20,
    min_importance:int=1,
)->list[dict]:
    """
    Mostra tutte le memorie salvate, dalla più recente.
    Usa quando l'utente chiede: 'cosa ho salvato?', 'mostrami le mie note',
    'lista delle memorie'.
    """

    conn = _get_db()
    rows = conn.execute(
        "SELECT id, created, topic, content, tags, importance, source FROM memories WHERE importance >= ? ORDER BY created DESC LIMIT ?",
        (min_importance, limit)
    ).fetchall()
    conn.close()

    return [
        {
            "id": row[0],
            "date": row[1][:10],
            "topic": row[2],
            "content": row[3],
            "tags": json.loads(row[4]) if row[4] else [],
            "importance": row[5],
            "source": row[6],
        }
        for row in rows
    ]

# tool 5 export di tutto in un unico file
def export_knowledge_base(filename: str='')->dict:
    
    """
    Esporta tutte le memorie in un unico file .md ordinato per topic.
    Ottimo per portare il contesto in una nuova chat o condividere con il team.
    """
    conn = _get_db()
    rows = conn.execute(
        "SELECT created, topic, content, tags, importance FROM memories ORDER BY importance DESC, created DESC"
    ).fetchall()
    conn.close()

    if not rows:
        return {"message" : "Nessuna memoria salvata."}
    
    now = datetime.now()
    date_str = now.strftime("%Y-%m-%d_%H-%M-%S")

    if not filename:
        filename = f"knowledge_base_{date_str}.md"

    filepath = BASE_DIR / filename

    md = f"# Knowledge Base - {date_str}\n\n"
    md += f"*{len(rows)} memorie esportate*\n\n---\n\n"

    for r in rows:
        stars = "*" * r[4]
        tags = json.loads(r[3]) if r[3] else []
        tag_str = " ".join(f"#{t}" for t in tags)
        md += f"## {r[1]}\n\n"
        md += f"{stars} {tag_str}\n"
        md += f"*{r[0][:10]}*\n\n"
        md += f"{r[2]}\n\n---\n\n"

    filepath.write_text(md, encoding="utf-8")

    return {
        "saved_to": str(filepath),
        "message":  f"Knowledge Base esportata in {filepath}",
        "total_items" : len(rows),
    }


if __name__ == "__main__":
    mcp.run(transport="stdio")