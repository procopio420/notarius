'use client'

import React, { useCallback, useEffect, useRef, useState } from 'react'
import { useEditor, EditorContent } from '@tiptap/react'
import StarterKit from '@tiptap/starter-kit'
import Placeholder from '@tiptap/extension-placeholder'
import TextAlign from '@tiptap/extension-text-align'
import { Box, Typography, Button, IconButton, Tooltip } from '@mui/material'
import {
  FormatBold,
  FormatItalic,
  FormatListBulleted,
  FormatListNumbered,
  FormatAlignLeft,
  FormatAlignCenter,
  FormatAlignRight,
  FormatAlignJustify
} from '@mui/icons-material'

interface RichTextEditorProps {
  content: string
  onChange: (content: string) => void
  onSelectionChange?: (selectedText: string) => void
  placeholder?: string
  editable?: boolean
  className?: string
}

// Function to convert basic markdown to HTML
const markdownToHtml = (markdown: string): string => {
  if (!markdown) return ''
  
  let html = markdown
  
  // Convert basic markdown syntax to HTML
  // Bold text: **text** -> <strong>text</strong>
  html = html.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
  
  // Italic text: *text* -> <em>text</em>
  html = html.replace(/\*(.*?)\*/g, '<em>$1</em>')
  
  // Headers: # Header -> <h1>Header</h1>
  html = html.replace(/^### (.*$)/gim, '<h3>$1</h3>')
  html = html.replace(/^## (.*$)/gim, '<h2>$1</h2>')
  html = html.replace(/^# (.*$)/gim, '<h1>$1</h1>')
  
  // Convert line breaks to proper HTML structure
  // Split by double line breaks first
  const paragraphs = html.split(/\n\s*\n/)
  
  // Process each paragraph
  html = paragraphs.map(paragraph => {
    paragraph = paragraph.trim()
    if (!paragraph) return ''
    
    // If it's already a header, don't wrap in p
    if (paragraph.startsWith('<h')) {
      return paragraph
    }
    
    // Convert single line breaks to <br>
    paragraph = paragraph.replace(/\n/g, '<br>')
    
    // Wrap in paragraph
    return `<p>${paragraph}</p>`
  }).join('')
  
  return html
}

export function RichTextEditor({
  content,
  onChange,
  onSelectionChange,
  placeholder = 'Digite o conteúdo do documento...',
  editable = true,
  className = ''
}: RichTextEditorProps) {
  const editorRef = useRef<HTMLDivElement>(null)
  const [isMounted, setIsMounted] = useState(false)

  // Handle client-side mounting
  useEffect(() => {
    setIsMounted(true)
  }, [])

  const editor = useEditor({
    extensions: [
      StarterKit.configure({
        heading: {
          levels: [1, 2, 3, 4, 5, 6],
        },
        paragraph: {
          HTMLAttributes: {
            class: 'prose-paragraph',
          },
        },
        bulletList: {
          HTMLAttributes: {
            class: 'prose-list',
          },
        },
        orderedList: {
          HTMLAttributes: {
            class: 'prose-list',
          },
        },
      }),
      Placeholder.configure({
        placeholder,
      }),
      TextAlign.configure({
        types: ['heading', 'paragraph'],
      }),
    ],
    content: markdownToHtml(content),
    editable,
    immediatelyRender: false, // Fix SSR hydration mismatch
    onUpdate: ({ editor }) => {
      onChange(editor.getHTML())
    },
    onSelectionUpdate: ({ editor }) => {
      const { from, to } = editor.state.selection
      if (from !== to) {
        const selectedText = editor.state.doc.textBetween(from, to)
        onSelectionChange?.(selectedText)
      } else {
        onSelectionChange?.('')
      }
    },
    editorProps: {
      attributes: {
        class: 'prose prose-sm sm:prose lg:prose-lg xl:prose-2xl mx-auto focus:outline-none',
        style: 'line-height: 1.6; padding: 16px; min-height: 400px;'
      },
    },
  })

  // Update content when prop changes
  useEffect(() => {
    if (editor && content !== editor.getHTML()) {
      const htmlContent = markdownToHtml(content)
      editor.commands.setContent(htmlContent, false)
    }
  }, [content, editor])

  // Update editable state
  useEffect(() => {
    if (editor) {
      editor.setEditable(editable)
    }
  }, [editor, editable])

  const toggleBold = useCallback(() => {
    editor?.chain().focus().toggleBold().run()
  }, [editor])

  const toggleItalic = useCallback(() => {
    editor?.chain().focus().toggleItalic().run()
  }, [editor])

  const toggleHeading = useCallback((level: 1 | 2 | 3 | 4 | 5 | 6) => {
    editor?.chain().focus().toggleHeading({ level }).run()
  }, [editor])

  const toggleBulletList = useCallback(() => {
    editor?.chain().focus().toggleBulletList().run()
  }, [editor])

  const toggleOrderedList = useCallback(() => {
    editor?.chain().focus().toggleOrderedList().run()
  }, [editor])

  const setTextAlign = useCallback((alignment: 'left' | 'center' | 'right' | 'justify') => {
    editor?.chain().focus().setTextAlign(alignment).run()
  }, [editor])


  // Show loading state during SSR or before client-side mounting
  if (!isMounted || !editor) {
    return (
      <Box 
        sx={{ 
          border: 1, 
          borderColor: 'divider', 
          borderRadius: 1, 
          bgcolor: 'background.paper',
          minHeight: 400,
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          p: 2
        }}
      >
        <Typography color="text.secondary">Carregando editor...</Typography>
      </Box>
    )
  }

  return (
    <>
      <style jsx global>{`
        .ProseMirror {
          line-height: 1.6;
          padding: 16px;
          min-height: 400px;
          font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Roboto', 'Oxygen', 'Ubuntu', 'Cantarell', 'Fira Sans', 'Droid Sans', 'Helvetica Neue', sans-serif;
          font-size: 14px;
          color: #333;
        }
        .ProseMirror p {
          margin-bottom: 1em;
          margin-top: 0;
        }
        .ProseMirror h1, .ProseMirror h2, .ProseMirror h3, .ProseMirror h4, .ProseMirror h5, .ProseMirror h6 {
          margin-top: 1.5em;
          margin-bottom: 0.5em;
          font-weight: 600;
          line-height: 1.2;
        }
        .ProseMirror h1 { font-size: 1.5em; }
        .ProseMirror h2 { font-size: 1.3em; }
        .ProseMirror h3 { font-size: 1.1em; }
        .ProseMirror ul, .ProseMirror ol {
          margin: 1em 0;
          padding-left: 2em;
        }
        .ProseMirror li {
          margin: 0.5em 0;
          line-height: 1.4;
        }
        .ProseMirror strong {
          font-weight: 600;
        }
        .ProseMirror em {
          font-style: italic;
        }
        .ProseMirror blockquote {
          margin: 1em 0;
          padding-left: 1em;
          border-left: 3px solid #ddd;
          font-style: italic;
        }
        .ProseMirror hr {
          margin: 2em 0;
          border: none;
          border-top: 1px solid #ddd;
        }
        .ProseMirror code {
          background-color: #f5f5f5;
          padding: 2px 4px;
          border-radius: 3px;
          font-family: 'Monaco', 'Menlo', 'Ubuntu Mono', monospace;
          font-size: 0.9em;
        }
        .ProseMirror pre {
          background-color: #f5f5f5;
          padding: 1em;
          border-radius: 5px;
          overflow-x: auto;
          margin: 1em 0;
        }
        .ProseMirror pre code {
          background: none;
          padding: 0;
        }
      `}</style>
      <Box 
        sx={{ 
          border: 1, 
          borderColor: 'divider', 
          borderRadius: 1, 
          bgcolor: 'background.paper',
          minHeight: 400
        }}
      >
      {/* Toolbar */}
      {editable && (
        <Box 
          sx={{ 
            borderBottom: 1, 
            borderColor: 'divider', 
            p: 1, 
            display: 'flex', 
            flexWrap: 'wrap', 
            gap: 0.5 
          }}
        >
          {/* Text formatting */}
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5, borderRight: 1, borderColor: 'divider', pr: 1, mr: 1 }}>
            <Tooltip title="Negrito">
              <IconButton
                size="small"
                onClick={toggleBold}
                color={editor.isActive('bold') ? 'primary' : 'default'}
              >
                <FormatBold />
              </IconButton>
            </Tooltip>
            <Tooltip title="Itálico">
              <IconButton
                size="small"
                onClick={toggleItalic}
                color={editor.isActive('italic') ? 'primary' : 'default'}
              >
                <FormatItalic />
              </IconButton>
            </Tooltip>
          </Box>

          {/* Headings */}
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5, borderRight: 1, borderColor: 'divider', pr: 1, mr: 1 }}>
            <Tooltip title="Título 1">
              <Button
                size="small"
                onClick={() => toggleHeading(1)}
                variant={editor.isActive('heading', { level: 1 }) ? 'contained' : 'outlined'}
                sx={{ minWidth: 'auto', px: 1 }}
              >
                H1
              </Button>
            </Tooltip>
            <Tooltip title="Título 2">
              <Button
                size="small"
                onClick={() => toggleHeading(2)}
                variant={editor.isActive('heading', { level: 2 }) ? 'contained' : 'outlined'}
                sx={{ minWidth: 'auto', px: 1 }}
              >
                H2
              </Button>
            </Tooltip>
            <Tooltip title="Título 3">
              <Button
                size="small"
                onClick={() => toggleHeading(3)}
                variant={editor.isActive('heading', { level: 3 }) ? 'contained' : 'outlined'}
                sx={{ minWidth: 'auto', px: 1 }}
              >
                H3
              </Button>
            </Tooltip>
          </Box>

          {/* Lists */}
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5, borderRight: 1, borderColor: 'divider', pr: 1, mr: 1 }}>
            <Tooltip title="Lista com marcadores">
              <IconButton
                size="small"
                onClick={toggleBulletList}
                color={editor.isActive('bulletList') ? 'primary' : 'default'}
              >
                <FormatListBulleted />
              </IconButton>
            </Tooltip>
            <Tooltip title="Lista numerada">
              <IconButton
                size="small"
                onClick={toggleOrderedList}
                color={editor.isActive('orderedList') ? 'primary' : 'default'}
              >
                <FormatListNumbered />
              </IconButton>
            </Tooltip>
          </Box>

          {/* Text alignment */}
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
            <Tooltip title="Alinhar à esquerda">
              <IconButton
                size="small"
                onClick={() => setTextAlign('left')}
                color={editor.isActive({ textAlign: 'left' }) ? 'primary' : 'default'}
              >
                <FormatAlignLeft />
              </IconButton>
            </Tooltip>
            <Tooltip title="Centralizar">
              <IconButton
                size="small"
                onClick={() => setTextAlign('center')}
                color={editor.isActive({ textAlign: 'center' }) ? 'primary' : 'default'}
              >
                <FormatAlignCenter />
              </IconButton>
            </Tooltip>
            <Tooltip title="Alinhar à direita">
              <IconButton
                size="small"
                onClick={() => setTextAlign('right')}
                color={editor.isActive({ textAlign: 'right' }) ? 'primary' : 'default'}
              >
                <FormatAlignRight />
              </IconButton>
            </Tooltip>
            <Tooltip title="Justificar">
              <IconButton
                size="small"
                onClick={() => setTextAlign('justify')}
                color={editor.isActive({ textAlign: 'justify' }) ? 'primary' : 'default'}
              >
                <FormatAlignJustify />
              </IconButton>
            </Tooltip>
          </Box>

        </Box>
      )}

      {/* Editor content */}
      <Box sx={{ p: 2, minHeight: 400 }}>
        <EditorContent editor={editor} ref={editorRef} />
      </Box>
      </Box>
    </>
  )
}
