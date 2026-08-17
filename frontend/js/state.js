// State client sederhana (single source of truth di sisi UI).
export const state = {
  libraryRoot: "",
  libraryRoots: [],      // Mendukung multiple folder library
  novels: [],
  activeNovelId: null,
  activeNovelFolder: "",
  activeNovelTitle: "",
  chapters: [],          // [{ref, novel_id, title, source, sort_key, has_original, index}]
  activeChapterRef: null,
  currentChapterData: null, // Cache data chapter aktif (hindari refetch saat toggle teks asli)
  bookmarks: [],         // [{id, chapter_index, label, created_at}]
  readSet: new Set(),    // chapter_index yang sudah dibaca (auto)
  settings: {
    font_size: 16,
    line_spacing: 1.7,
    paragraph_indent: 28,
    page_margin: 24,
    read_width: 720,
    theme: "light",
    show_original: false,
  },
  showOriginal: false,
  novelFilter: "",       // Filter pencarian novel pada panel koleksi
  chapterFilter: "",     // Filter pencarian chapter
};

export function setActiveNovel(novel) {
  state.activeNovelId = novel ? novel.id : null;
  state.activeNovelFolder = novel ? novel.folder_path : "";
  state.activeNovelTitle = novel ? novel.judul : "";
  state.activeChapterRef = null;
  state.currentChapterData = null;
}
