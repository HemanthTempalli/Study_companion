# Known Limitations

## 1. Single File Format
- Only PDF uploads are supported
- DOCX, PPTX, images, and video are not processed
- **Mitigation**: PDF is the most common academic format

## 2. No Real-Time Processing
- Document processing is async via polling (5-second intervals)
- No WebSocket for live status updates
- **Mitigation**: Frontend polls every 5 seconds during processing

## 3. Single-User Projects
- Projects are owned by one user
- No shared projects or collaborative learning
- **Mitigation**: Admin can inspect any user's journey

## 4. No Social Login
- Only email/password authentication
- No Google, GitHub, or OAuth providers
- **Mitigation**: Simple registration flow, demo accounts provided

## 5. Local File Storage
- Uploaded PDFs stored on local filesystem
- No S3/GCS integration
- **Mitigation**: Works for prototype; easy to swap storage backend

## 6. No Rate Limiting
- API has no per-user rate limiting
- Groq API has its own limits (14,400 req/day)
- **Mitigation**: For prototype/demo use, this is acceptable

## 7. Embedding Model Quality
- `all-MiniLM-L6-v2` is a lightweight model (384 dimensions)
- Higher quality models like `text-embedding-3-large` (3072 dim) exist but require API keys
- **Mitigation**: For educational content, MiniLM performs adequately for retrieval

## 8. No Offline Support
- Requires active internet connection for AI features
- Embeddings are generated locally but LLM calls need Groq API
- **Mitigation**: Material upload and reading could work offline; AI features inherently need connectivity

## 9. No Multi-Language Support
- UI is English-only
- AI responses are in English
- **Mitigation**: LLM can handle non-English content in PDFs

## 10. Test Coverage
- Integration tests for critical paths exist
- No comprehensive unit test suite
- No E2E tests (Cypress/Playwright)
- **Mitigation**: All critical flows have been manually tested end-to-end
