import { useEffect, useMemo, useState } from "react";
import { EditorContent, useEditor } from "@tiptap/react";
import StarterKit from "@tiptap/starter-kit";

type Note = {
  id: string;
  name: string;
  content: string;
};

const initialNotes: Note[] = [
  {
    id: "design",
    name: "design.md",
    content: "<h1>Chronos</h1><p>History travels with the Markdown file.</p><h2>Prototype boundary</h2><p>This UI is intentionally not connected to the Python history core.</p>",
  },
  {
    id: "ideas",
    name: "ideas.md",
    content: "<h1>Ideas</h1><ul><li>Portable document history</li><li>Explicit version restore</li><li>Readable Markdown outside Chronos</li></ul>",
  },
  {
    id: "tradeoffs",
    name: "tradeoffs.md",
    content: "<h1>Trade-offs</h1><p>Embedded history improves portability but increases file size and source noise.</p>",
  },
];

function App() {
  const [notes, setNotes] = useState(initialNotes);
  const [selectedId, setSelectedId] = useState(initialNotes[0].id);
  const [savedHtml, setSavedHtml] = useState(initialNotes[0].content);

  const selected = useMemo(
    () => notes.find((note) => note.id === selectedId) ?? notes[0],
    [notes, selectedId],
  );

  const editor = useEditor({
    extensions: [StarterKit],
    content: selected.content,
  });

  useEffect(() => {
    if (!editor) return;
    editor.commands.setContent(selected.content, false);
    setSavedHtml(selected.content);
  }, [editor, selected.id]);

  const currentHtml = editor?.getHTML() ?? selected.content;
  const dirty = currentHtml !== savedHtml;

  function chooseNote(note: Note) {
    if (!editor) return;
    const updated = editor.getHTML();
    setNotes((current) =>
      current.map((item) => (item.id === selected.id ? { ...item, content: updated } : item)),
    );
    setSelectedId(note.id);
  }

  function savePrototypeState() {
    if (!editor) return;
    const updated = editor.getHTML();
    setNotes((current) =>
      current.map((item) => (item.id === selected.id ? { ...item, content: updated } : item)),
    );
    setSavedHtml(updated);
  }

  return (
    <div className="app-shell">
      <header className="topbar">
        <div>
          <strong>Chronos</strong>
          <span className="prototype-pill">editor prototype</span>
        </div>
        <div className="topbar-actions">
          <span className={dirty ? "status dirty" : "status"}>{dirty ? "Unsaved" : "Saved"}</span>
          <button type="button" onClick={savePrototypeState} disabled={!editor || !dirty}>
            Save prototype state
          </button>
        </div>
      </header>

      <div className="workspace">
        <aside className="sidebar">
          <div className="sidebar-heading">Files</div>
          <nav>
            {notes.map((note) => (
              <button
                type="button"
                className={note.id === selected.id ? "file-row active" : "file-row"}
                key={note.id}
                onClick={() => chooseNote(note)}
              >
                <span className="file-icon">M</span>
                {note.name}
              </button>
            ))}
          </nav>
          <div className="boundary-note">
            This renderer demonstrates the editing surface only. Version history is implemented separately in <code>backend/</code>.
          </div>
        </aside>

        <main className="editor-pane">
          <div className="document-header">
            <div>
              <div className="eyebrow">Markdown document</div>
              <h1>{selected.name}</h1>
            </div>
            <div className="history-placeholder" aria-label="history integration status">
              History core: not connected
            </div>
          </div>
          <EditorContent editor={editor} className="editor-surface" />
        </main>
      </div>
    </div>
  );
}

export default App;
