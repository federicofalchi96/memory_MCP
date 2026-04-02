# Memory MCP Server

Memory MCP è un sistema di memoria persistente per agenti AI basato su MCP (Model Context Protocol).
Permette di salvare, recuperare e organizzare informazioni nel tempo, combinando database SQLite e file Markdown compatibili con Obsidian.

---

## Features

* Salvataggio strutturato di memorie (topic, contenuto, tag)
* Sistema di importanza (priorità da 1 a 5)
* Ricerca per keyword e tag
* Esportazione automatica in file Markdown
* Compatibilità con Obsidian (note locali)
* Salvataggio automatico dei riassunti chat
* Generazione knowledge base completa

---

## Architettura

Il sistema utilizza:

* MCP per esporre i tool
* SQLite per la persistenza strutturata
* File Markdown per lettura umana e integrazione con editor

Struttura directory:

```id="mem1"
ai-memory/
├── memories.db
├── notes/
├── kb/
```

---

## Installazione

```bash id="mem2"
git clone https://github.com/tuo-username/memory-mcp.git
cd memory-mcp
pip install -r requirements.txt
```

---

## Configurazione

Crea un file `.env`:

```env id="mem3"
CURR_DIR=/path/to/ai-memory
```

Se non impostato, usa automaticamente:

```id="mem4"
~/ai-memory
```

---

## Avvio

```bash id="mem5"
python main.py
```

---

## Database

Tabella principale:

```sql id="mem6"
memories (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    created TEXT,
    topic TEXT,
    content TEXT,
    tags TEXT,
    importance INTEGER,
    source TEXT
)
```

---

## Tools disponibili

### save_memory

Salva una nuova memoria.

```python id="mem7"
save_memory(
    topic="Progetto FOMO AI",
    content="Usare agentic RAG con caching",
    tags=["ai", "progetto"],
    importance=4
)
```

---

### recall_memory

Cerca memorie salvate.

```python id="mem8"
recall_memory(
    query="FOMO",
    tags=["ai"],
    min_importance=3
)
```

Restituisce risultati ordinati per:

* importanza
* data

---

### list_memories

Mostra le memorie recenti.

```python id="mem9"
list_memories(limit=20)
```

---

### save_chat_summary

Salva un riassunto della conversazione.

```python id="mem10"
save_chat_summary(
    summary="Discussione su sistema AI",
    key_decisions=["Usare MCP", "Aggiungere caching"],
    action_items=["Implementare embeddings"],
    topic="FOMO AI Sessione 1",
    tags=["ai", "chat"]
)
```

Output:

* file Markdown
* memoria salvata nel database

---

### export_knowledge_base

Esporta tutte le memorie in un file unico.

```python id="mem11"
export_knowledge_base()
```

Genera:

* file `.md` completo
* ordinato per importanza e data

---

## Formato file Markdown

Ogni memoria viene salvata come:

```markdown id="mem12"
---
id: 1
created: 2026-04-02
topic: Esempio
tags: ["ai", "note"]
importance: 3
source: chat
---

# Esempio

*** #ai #note

Contenuto della memoria
```

---

## Logica di funzionamento

1. L’utente salva una memoria
2. Il sistema:

   * scrive su SQLite
   * crea file Markdown
3. Le memorie possono essere:

   * cercate
   * filtrate
   * esportate

---

## Use case

* Memoria persistente per agenti AI
* Knowledge base personale
* Tracking decisioni progetto
* Diario tecnico sviluppatore
* Integrazione con Obsidian

---

## Roadmap

* Ricerca semantica (embeddings)
* Ranking intelligente delle memorie
* Sistema multi-utente
* Sync cloud
* Dashboard web

---

## Autore

Federico Falchi
Software Developer

---

## License

MIT
