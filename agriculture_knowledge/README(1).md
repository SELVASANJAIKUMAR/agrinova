# AgriNova Agriculture Knowledge Base

## Purpose

This knowledge base is designed to support an AI-powered agriculture platform (AgriNova) with reliable, source-grounded agricultural information suitable for Retrieval-Augmented Generation (RAG).

It provides practical agricultural guidance for farmers in India, with primary focus on South Indian context where available.

## Structure

```
agriculture_knowledge/
├── crops/              # Crop-specific cultivation guides
├── soil/               # Soil types and management
├── fertilizers/        # Nutrient and fertilizer information
├── irrigation/         # Water management and irrigation methods
├── pests/              # Common pests and management
├── diseases/           # Crop diseases and management
├── farming_practices/  # General agricultural practices
└── faq/                # Practical farmer FAQs
```

## Key Principles

### 1. Source-Grounded Information
- All significant claims reference authoritative sources
- Primarily uses ICAR, agricultural universities, government departments
- Avoids unverified blogs and commercial sources
- Clearly distinguishes verified facts from general principles

### 2. Regional Awareness
- Acknowledges regional variations in soil, climate, rainfall
- Specifies location context (e.g., Tamil Nadu, India generally)
- Recommends verification with local agricultural experts
- Avoids presenting region-specific advice as universal

### 3. RAG Optimization
- Documents organized into small, independent units
- Each section is self-contained and retrievable
- Metadata included for filtering and context
- Clear headings and logical structure

### 4. Agricultural Safety
- No fabricated fertilizer dosages
- No invented pesticide recommendations
- Emphasizes Integrated Pest Management (IPM)
- Recommends professional consultation where appropriate
- No human medical content

### 5. Transparency
- Clearly marks uncertainties and requirements for verification
- Specifies when information is soil/crop/variety/stage-dependent
- Distinguishes general principles from exact prescriptions
- Notes when information could not be reliably verified

## Document Metadata

Every document includes frontmatter with:
- `title`: Document name
- `category`: Knowledge category
- `crop` or `topic`: Specific subject
- `region`: Geographic context (India, Tamil Nadu, India-wide, etc.)
- `source_type`: Type of source (Agricultural University, Government, etc.)
- `source`: Source organization name
- `source_url`: URL if available
- `last_verified`: Date of verification

## Using This Knowledge Base

### For RAG Implementation
1. Use INDEX.md to map documents to topics
2. Use metadata for filtering by crop, region, category
3. Implement chunking based on heading levels (H1/H2/H3)
4. Combine metadata with semantic search for better retrieval

### For Chatbot Queries
1. Retrieve relevant documents based on farmer question
2. Extract specific sections for context
3. Use metadata to ensure regional relevance
4. Highlight uncertainties and recommend professional consultation

## Content Guidelines

### What IS Included
- Crop cultivation practices
- Soil management
- General nutrient principles (not exact dosages without sources)
- Irrigation concepts and methods
- Pest and disease identification
- Prevention and management strategies
- Good agricultural practices
- Practical farmer FAQs

### What IS NOT Included
- Exact fertilizer dosages (unless source-verified and context-specified)
- Pesticide names, doses, or mixing ratios (unless source-verified)
- Human medical information
- Veterinary information (except where clearly agricultural)
- Commercial product endorsements
- Speculative or unverified agricultural claims

## Quality Assurance

Each document has been checked for:
- ✓ Source verification
- ✓ No contradictory recommendations
- ✓ Appropriate regional context
- ✓ Clear uncertainty marking
- ✓ Proper citations
- ✓ No hallucinated agricultural information
- ✓ Relevant to Indian farmers
- ✓ RAG-optimized structure

## Sources Used

Complete bibliography available in SOURCES.md

Primary sources:
- Indian Council of Agricultural Research (ICAR)
- State Agricultural Universities (TNAU, PAU, etc.)
- Ministry of Agriculture & Farmers Welfare
- Krishi Vigyan Kendras
- Agricultural university research publications
- FAO guidelines (for general concepts)

## Version and Maintenance

- **Version**: 1.0
- **Created**: August 2026
- **Last Updated**: August 30, 2026
- **Maintenance**: Documents should be verified annually with latest ICAR/university recommendations

## Contact and Updates

For updates or additional information, consult:
- Local agricultural extension offices
- State agricultural universities
- Krishi Vigyan Kendras (KVKs)
- Ministry of Agriculture official channels

---

**Note**: This knowledge base is optimized for RAG integration and provides foundational agricultural knowledge. For crop-specific issues, local soil conditions, or unusual situations, farmers should consult local agricultural experts and extension services.
