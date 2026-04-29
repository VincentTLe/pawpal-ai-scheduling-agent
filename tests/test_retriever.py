def test_preview_preserves_markdown_line_breaks():
    from retriever import RetrievedChunk

    chunk = RetrievedChunk(
        source="dog_care.md",
        heading="Walking",
        text="Intro line.\n\nFor scheduling purposes:\n- Walk daily\n- Keep it safe\nFinal line.",
        score=5,
    )

    preview = chunk.preview(max_lines=5)

    assert "For scheduling purposes:" in preview
    assert "- Walk daily" in preview
    assert "\n" in preview
