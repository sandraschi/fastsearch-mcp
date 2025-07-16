import React, { useState, useRef } from 'react';
import {
  Box,
  Paper,
  Typography,
  TextField,
  Button,
  Grid,
  Card,
  CardContent,
  Select,
  MenuItem,
  FormControl,
  InputLabel,
  Stepper,
  Step,
  StepLabel,
  StepContent,
  Alert,
  LinearProgress,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  IconButton,
  Tabs,
  Tab,
  List,
  ListItem,
  ListItemText,
  ListItemSecondaryAction,
  Chip,
  Accordion,
  AccordionSummary,
  AccordionDetails,
  Slider
} from '@mui/material';
import {
  MenuBook,
  Edit,
  Download,
  Share,
  Refresh,
  Add,
  Remove,
  ExpandMore,
  Visibility,
  Print,
  Save,
  Delete,
  LibraryBooks,
  CreateNewFolder,
  Description,
  Settings,
  History
} from '@mui/icons-material';
import axios from 'axios';

const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:4700';

// Book genres and types
const BOOK_GENRES = [
  { id: 'fiction', name: 'Fiction', description: 'Imaginative and creative storytelling' },
  { id: 'non_fiction', name: 'Non-Fiction', description: 'Factual and informational content' },
  { id: 'mystery', name: 'Mystery', description: 'Suspenseful and puzzle-solving stories' },
  { id: 'romance', name: 'Romance', description: 'Love and relationship-focused stories' },
  { id: 'sci_fi', name: 'Science Fiction', description: 'Futuristic and technological themes' },
  { id: 'fantasy', name: 'Fantasy', description: 'Magical and mythical worlds' },
  { id: 'thriller', name: 'Thriller', description: 'High-tension and suspenseful narratives' },
  { id: 'biography', name: 'Biography', description: 'Life stories of real people' },
  { id: 'self_help', name: 'Self-Help', description: 'Personal development and guidance' },
  { id: 'children', name: 'Children\'s Book', description: 'Stories for young readers' }
];

const WRITING_STYLES = [
  { id: 'narrative', name: 'Narrative', description: 'Story-driven with characters and plot' },
  { id: 'descriptive', name: 'Descriptive', description: 'Rich in detail and imagery' },
  { id: 'conversational', name: 'Conversational', description: 'Informal and engaging tone' },
  { id: 'academic', name: 'Academic', description: 'Scholarly and research-based' },
  { id: 'journalistic', name: 'Journalistic', description: 'Factual and news-style writing' },
  { id: 'poetic', name: 'Poetic', description: 'Lyrical and artistic language' }
];

const BOOK_LENGTHS = [
  { id: 'short', name: 'Short Story', pages: '10-20', words: '2,500-5,000' },
  { id: 'novella', name: 'Novella', pages: '50-100', words: '17,500-40,000' },
  { id: 'novel', name: 'Novel', pages: '200-400', words: '80,000-120,000' },
  { id: 'epic', name: 'Epic Novel', pages: '400+', words: '120,000+' }
];

// Chapter editor component
const ChapterEditor = ({ chapter, onUpdate, onDelete, index }) => {
  const [expanded, setExpanded] = useState(false);

  return (
    <Accordion expanded={expanded} onChange={() => setExpanded(!expanded)}>
      <AccordionSummary expandIcon={<ExpandMore />}>
        <Box sx={{ display: 'flex', alignItems: 'center', width: '100%' }}>
          <Typography variant="h6" sx={{ flexGrow: 1 }}>
            Chapter {index + 1}: {chapter.title || 'Untitled Chapter'}
          </Typography>
          <Chip
            label={`${chapter.content ? chapter.content.split(' ').length : 0} words`}
            size="small"
            variant="outlined"
          />
        </Box>
      </AccordionSummary>
      <AccordionDetails>
        <Grid container spacing={2}>
          <Grid item xs={12}>
            <TextField
              fullWidth
              label="Chapter Title"
              value={chapter.title || ''}
              onChange={(e) => onUpdate({ ...chapter, title: e.target.value })}
            />
          </Grid>
          <Grid item xs={12}>
            <TextField
              fullWidth
              multiline
              rows={6}
              label="Chapter Outline"
              placeholder="Outline the key events and developments in this chapter..."
              value={chapter.outline || ''}
              onChange={(e) => onUpdate({ ...chapter, outline: e.target.value })}
            />
          </Grid>
          <Grid item xs={12}>
            <TextField
              fullWidth
              multiline
              rows={12}
              label="Chapter Content"
              placeholder="Chapter content will be generated here..."
              value={chapter.content || ''}
              onChange={(e) => onUpdate({ ...chapter, content: e.target.value })}
            />
          </Grid>
          <Grid item xs={6}>
            <TextField
              fullWidth
              type="number"
              label="Target Word Count"
              value={chapter.target_words || 1000}
              onChange={(e) => onUpdate({ ...chapter, target_words: parseInt(e.target.value) })}
              inputProps={{ min: 100, max: 10000 }}
            />
          </Grid>
          <Grid item xs={6}>
            <Box sx={{ display: 'flex', gap: 1, alignItems: 'center', height: '100%' }}>
              <Button variant="outlined" onClick={() => onDelete(index)} color="error">
                Delete Chapter
              </Button>
            </Box>
          </Grid>
        </Grid>
      </AccordionDetails>
    </Accordion>
  );
};

// Book preview component
const BookPreview = ({ book, onClose }) => {
  const [currentPage, setCurrentPage] = useState(0);
  
  const downloadBook = () => {
    const content = `
# ${book.title}
${book.author ? `*by ${book.author}*` : ''}

${book.summary || ''}

${book.chapters.map((chapter, index) => `
## Chapter ${index + 1}: ${chapter.title}

${chapter.content}
`).join('\n')}
    `;
    
    const blob = new Blob([content], { type: 'text/markdown' });
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `${book.title.replace(/\s+/g, '_')}.md`;
    a.click();
    window.URL.revokeObjectURL(url);
  };

  return (
    <Dialog open={true} onClose={onClose} maxWidth="md" fullWidth>
      <DialogTitle>
        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <Typography variant="h6">{book.title}</Typography>
          <Box>
            <IconButton onClick={downloadBook}>
              <Download />
            </IconButton>
            <IconButton onClick={onClose}>
              <Visibility />
            </IconButton>
          </Box>
        </Box>
      </DialogTitle>
      <DialogContent>
        <Box sx={{ minHeight: 400, maxHeight: 600, overflow: 'auto', p: 2 }}>
          {book.chapters.length > 0 && (
            <Box>
              <Tabs value={currentPage} onChange={(e, newValue) => setCurrentPage(newValue)} sx={{ mb: 2 }}>
                {book.chapters.map((chapter, index) => (
                  <Tab key={index} label={`Ch. ${index + 1}`} />
                ))}
              </Tabs>
              
              {book.chapters[currentPage] && (
                <Box>
                  <Typography variant="h5" gutterBottom>
                    {book.chapters[currentPage].title}
                  </Typography>
                  <Typography variant="body1" sx={{ whiteSpace: 'pre-wrap', lineHeight: 1.8 }}>
                    {book.chapters[currentPage].content}
                  </Typography>
                </Box>
              )}
            </Box>
          )}
        </Box>
      </DialogContent>
      <DialogActions>
        <Button onClick={onClose}>Close</Button>
        <Button onClick={downloadBook} startIcon={<Download />}>
          Download Book
        </Button>
      </DialogActions>
    </Dialog>
  );
};

// Main Book Generator component
const BookGenerator = () => {
  const [activeStep, setActiveStep] = useState(0);
  const [activeTab, setActiveTab] = useState(0);
  
  // Book metadata
  const [title, setTitle] = useState('');
  const [author, setAuthor] = useState('');
  const [genre, setGenre] = useState('fiction');
  const [style, setStyle] = useState('narrative');
  const [length, setLength] = useState('novel');
  const [concept, setConcept] = useState('');
  const [summary, setSummary] = useState('');
  const [targetAudience, setTargetAudience] = useState('');
  
  // Chapters and content
  const [chapters, setChapters] = useState([]);
  const [outline, setOutline] = useState('');
  const [creativity, setCreativity] = useState(0.7);
  
  // Generation state
  const [generating, setGenerating] = useState(false);
  const [currentChapter, setCurrentChapter] = useState(0);
  const [progress, setProgress] = useState(0);
  
  // UI state
  const [bookProjects, setBookProjects] = useState([]);
  const [previewOpen, setPreviewOpen] = useState(false);
  const [currentBook, setCurrentBook] = useState(null);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');

  const getAuthHeaders = () => {
    const token = localStorage.getItem('token');
    return { Authorization: `Bearer ${token}` };
  };

  const generateOutline = async () => {
    if (!concept.trim()) {
      setError('Please provide a book concept');
      return;
    }

    setGenerating(true);
    setError('');

    try {
      const response = await axios.post(
        `${API_BASE_URL}/api/v1/book/generate-outline`,
        {
          title,
          concept,
          genre,
          style,
          length,
          target_audience: targetAudience
        },
        { headers: getAuthHeaders() }
      );

      setOutline(response.data.outline);
      setSummary(response.data.summary);
      setChapters(response.data.chapters.map((chapter, index) => ({
        id: Date.now() + index,
        title: chapter.title,
        outline: chapter.outline,
        content: '',
        target_words: chapter.target_words || 1000
      })));
      
      setActiveStep(1);
      setSuccess('Outline generated successfully!');

    } catch (error) {
      console.error('Outline generation error:', error);
      setError(error.response?.data?.detail || 'Failed to generate outline');
    } finally {
      setGenerating(false);
    }
  };

  const generateBook = async () => {
    if (chapters.length === 0) {
      setError('Please generate an outline first');
      return;
    }

    setGenerating(true);
    setCurrentChapter(0);
    setProgress(0);
    setError('');

    try {
      const response = await axios.post(
        `${API_BASE_URL}/api/v1/book/generate`,
        {
          title,
          author,
          genre,
          style,
          summary,
          chapters: chapters.map(chapter => ({
            title: chapter.title,
            outline: chapter.outline,
            target_words: chapter.target_words
          })),
          creativity
        },
        { headers: getAuthHeaders() }
      );

      // Poll for progress
      const bookId = response.data.book_id;
      pollBookProgress(bookId);

    } catch (error) {
      console.error('Book generation error:', error);
      setError(error.response?.data?.detail || 'Failed to generate book');
      setGenerating(false);
    }
  };

  const pollBookProgress = async (bookId) => {
    try {
      const response = await axios.get(
        `${API_BASE_URL}/api/v1/book/status/${bookId}`,
        { headers: getAuthHeaders() }
      );

      const { status, current_chapter, total_chapters, chapters: chapterContents } = response.data;

      setCurrentChapter(current_chapter);
      setProgress((current_chapter / total_chapters) * 100);

      if (status === 'completed') {
        // Update chapters with generated content
        const updatedChapters = chapters.map((chapter, index) => ({
          ...chapter,
          content: chapterContents[index]?.content || chapter.content
        }));
        
        setChapters(updatedChapters);
        setCurrentBook({
          title,
          author,
          genre,
          summary,
          chapters: updatedChapters,
          created_at: new Date().toISOString()
        });
        
        setGenerating(false);
        setActiveStep(2);
        setSuccess('Book generated successfully!');
        
      } else if (status === 'failed') {
        setGenerating(false);
        setError('Book generation failed');
      } else {
        // Continue polling
        setTimeout(() => pollBookProgress(bookId), 3000);
      }

    } catch (error) {
      console.error('Progress polling error:', error);
      setGenerating(false);
      setError('Failed to check book progress');
    }
  };

  const addChapter = () => {
    const newChapter = {
      id: Date.now(),
      title: `Chapter ${chapters.length + 1}`,
      outline: '',
      content: '',
      target_words: 1000
    };
    setChapters([...chapters, newChapter]);
  };

  const updateChapter = (index, updatedChapter) => {
    const newChapters = [...chapters];
    newChapters[index] = updatedChapter;
    setChapters(newChapters);
  };

  const deleteChapter = (index) => {
    const newChapters = chapters.filter((_, i) => i !== index);
    setChapters(newChapters);
  };

  const getTotalWords = () => {
    return chapters.reduce((total, chapter) => total + (chapter.content ? chapter.content.split(' ').length : 0), 0);
  };

  const TabPanel = ({ children, value, index, ...other }) => (
    <div
      role="tabpanel"
      hidden={value !== index}
      id={`book-tabpanel-${index}`}
      aria-labelledby={`book-tab-${index}`}
      {...other}
    >
      {value === index && (
        <Box sx={{ p: 3 }}>
          {children}
        </Box>
      )}
    </div>
  );

  const steps = [
    'Book Concept',
    'Outline & Chapters',
    'Generate Book'
  ];

  return (
    <Box sx={{ p: 3 }}>
      <Typography variant="h4" component="h1" gutterBottom>
        📚 Book Generator
      </Typography>
      <Typography variant="subtitle1" color="text.secondary" sx={{ mb: 3 }}>
        Create complete books with AI assistance. From concept to finished manuscript.
      </Typography>

      {error && <Alert severity="error" sx={{ mb: 2 }} onClose={() => setError('')}>{error}</Alert>}
      {success && <Alert severity="success" sx={{ mb: 2 }} onClose={() => setSuccess('')}>{success}</Alert>}

      <Grid container spacing={3}>
        {/* Main Content */}
        <Grid item xs={12} md={8}>
          <Paper sx={{ p: 3 }}>
            <Stepper activeStep={activeStep} orientation="vertical">
              {/* Step 1: Book Concept */}
              <Step>
                <StepLabel>Create Book Concept</StepLabel>
                <StepContent>
                  <Grid container spacing={3}>
                    <Grid item xs={12} sm={6}>
                      <TextField
                        fullWidth
                        label="Book Title"
                        value={title}
                        onChange={(e) => setTitle(e.target.value)}
                        placeholder="Enter your book title"
                      />
                    </Grid>
                    <Grid item xs={12} sm={6}>
                      <TextField
                        fullWidth
                        label="Author Name"
                        value={author}
                        onChange={(e) => setAuthor(e.target.value)}
                        placeholder="Your name or pen name"
                      />
                    </Grid>
                    <Grid item xs={12}>
                      <TextField
                        fullWidth
                        multiline
                        rows={4}
                        label="Book Concept"
                        value={concept}
                        onChange={(e) => setConcept(e.target.value)}
                        placeholder="Describe your book idea, main characters, plot, and themes..."
                      />
                    </Grid>
                    <Grid item xs={12} sm={4}>
                      <FormControl fullWidth>
                        <InputLabel>Genre</InputLabel>
                        <Select value={genre} onChange={(e) => setGenre(e.target.value)}>
                          {BOOK_GENRES.map((g) => (
                            <MenuItem key={g.id} value={g.id}>
                              <Box>
                                <Typography variant="body1">{g.name}</Typography>
                                <Typography variant="caption" color="text.secondary">
                                  {g.description}
                                </Typography>
                              </Box>
                            </MenuItem>
                          ))}
                        </Select>
                      </FormControl>
                    </Grid>
                    <Grid item xs={12} sm={4}>
                      <FormControl fullWidth>
                        <InputLabel>Writing Style</InputLabel>
                        <Select value={style} onChange={(e) => setStyle(e.target.value)}>
                          {WRITING_STYLES.map((s) => (
                            <MenuItem key={s.id} value={s.id}>
                              <Box>
                                <Typography variant="body1">{s.name}</Typography>
                                <Typography variant="caption" color="text.secondary">
                                  {s.description}
                                </Typography>
                              </Box>
                            </MenuItem>
                          ))}
                        </Select>
                      </FormControl>
                    </Grid>
                    <Grid item xs={12} sm={4}>
                      <FormControl fullWidth>
                        <InputLabel>Book Length</InputLabel>
                        <Select value={length} onChange={(e) => setLength(e.target.value)}>
                          {BOOK_LENGTHS.map((l) => (
                            <MenuItem key={l.id} value={l.id}>
                              <Box>
                                <Typography variant="body1">{l.name}</Typography>
                                <Typography variant="caption" color="text.secondary">
                                  {l.pages} pages ({l.words} words)
                                </Typography>
                              </Box>
                            </MenuItem>
                          ))}
                        </Select>
                      </FormControl>
                    </Grid>
                    <Grid item xs={12}>
                      <TextField
                        fullWidth
                        label="Target Audience (Optional)"
                        value={targetAudience}
                        onChange={(e) => setTargetAudience(e.target.value)}
                        placeholder="e.g., Young adults, Children 8-12, Business professionals..."
                      />
                    </Grid>
                    <Grid item xs={12}>
                      <Button
                        variant="contained"
                        onClick={generateOutline}
                        disabled={generating || !concept.trim()}
                        startIcon={generating ? <CreateNewFolder /> : <Description />}
                      >
                        {generating ? 'Generating Outline...' : 'Generate Outline & Chapters'}
                      </Button>
                    </Grid>
                  </Grid>
                </StepContent>
              </Step>

              {/* Step 2: Outline & Chapters */}
              <Step>
                <StepLabel>Edit Outline & Chapters</StepLabel>
                <StepContent>
                  <Tabs value={activeTab} onChange={(e, newValue) => setActiveTab(newValue)} sx={{ mb: 3 }}>
                    <Tab label="Book Outline" />
                    <Tab label="Chapters" />
                    <Tab label="Settings" />
                  </Tabs>

                  <TabPanel value={activeTab} index={0}>
                    <Grid container spacing={3}>
                      <Grid item xs={12}>
                        <TextField
                          fullWidth
                          multiline
                          rows={6}
                          label="Book Summary"
                          value={summary}
                          onChange={(e) => setSummary(e.target.value)}
                          placeholder="Overall book summary and plot..."
                        />
                      </Grid>
                      <Grid item xs={12}>
                        <TextField
                          fullWidth
                          multiline
                          rows={8}
                          label="Detailed Outline"
                          value={outline}
                          onChange={(e) => setOutline(e.target.value)}
                          placeholder="Detailed chapter-by-chapter outline..."
                        />
                      </Grid>
                    </Grid>
                  </TabPanel>

                  <TabPanel value={activeTab} index={1}>
                    <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
                      <Typography variant="h6">
                        Chapters ({chapters.length})
                      </Typography>
                      <Button
                        variant="outlined"
                        startIcon={<Add />}
                        onClick={addChapter}
                      >
                        Add Chapter
                      </Button>
                    </Box>

                    {chapters.map((chapter, index) => (
                      <ChapterEditor
                        key={chapter.id}
                        chapter={chapter}
                        index={index}
                        onUpdate={(updatedChapter) => updateChapter(index, updatedChapter)}
                        onDelete={deleteChapter}
                      />
                    ))}
                  </TabPanel>

                  <TabPanel value={activeTab} index={2}>
                    <Grid container spacing={3}>
                      <Grid item xs={12}>
                        <Typography gutterBottom>Writing Creativity</Typography>
                        <Slider
                          value={creativity}
                          onChange={(e, newValue) => setCreativity(newValue)}
                          min={0}
                          max={1}
                          step={0.1}
                          marks={[
                            { value: 0, label: 'Structured' },
                            { value: 0.5, label: 'Balanced' },
                            { value: 1, label: 'Creative' }
                          ]}
                        />
                      </Grid>
                    </Grid>
                  </TabPanel>

                  <Box sx={{ mt: 3 }}>
                    <Button
                      variant="contained"
                      onClick={generateBook}
                      disabled={generating || chapters.length === 0}
                      startIcon={generating ? <MenuBook /> : <CreateNewFolder />}
                    >
                      {generating ? 'Writing Book...' : 'Generate Complete Book'}
                    </Button>
                  </Box>
                </StepContent>
              </Step>

              {/* Step 3: Book Generation */}
              <Step>
                <StepLabel>Generate Complete Book</StepLabel>
                <StepContent>
                  {generating && (
                    <Box sx={{ mb: 3 }}>
                      <Typography variant="h6" gutterBottom>
                        Writing Your Book...
                      </Typography>
                      <LinearProgress variant="determinate" value={progress} sx={{ mb: 1 }} />
                      <Typography variant="body2" color="text.secondary">
                        Chapter {currentChapter + 1} of {chapters.length}
                      </Typography>
                    </Box>
                  )}

                  {currentBook && (
                    <Box>
                      <Typography variant="h6" gutterBottom>
                        Book Generated Successfully!
                      </Typography>
                      <Card sx={{ mb: 2 }}>
                        <CardContent>
                          <Typography variant="h5" gutterBottom>{currentBook.title}</Typography>
                          {currentBook.author && (
                            <Typography variant="subtitle1" color="text.secondary" gutterBottom>
                              by {currentBook.author}
                            </Typography>
                          )}
                          <Typography variant="body2" sx={{ mb: 2 }}>
                            {currentBook.summary}
                          </Typography>
                          <Box sx={{ display: 'flex', gap: 1, mb: 2 }}>
                            <Chip label={genre} />
                            <Chip label={`${currentBook.chapters.length} chapters`} />
                            <Chip label={`${getTotalWords()} words`} />
                          </Box>
                        </CardContent>
                      </Card>
                      
                      <Box sx={{ display: 'flex', gap: 2 }}>
                        <Button
                          variant="contained"
                          startIcon={<Visibility />}
                          onClick={() => setPreviewOpen(true)}
                        >
                          Preview Book
                        </Button>
                        <Button
                          variant="outlined"
                          startIcon={<Download />}
                          onClick={() => {
                            const content = `# ${currentBook.title}\n${currentBook.author ? `*by ${currentBook.author}*\n` : ''}\n${currentBook.summary}\n\n${currentBook.chapters.map((ch, i) => `## Chapter ${i+1}: ${ch.title}\n\n${ch.content}`).join('\n\n')}`;
                            const blob = new Blob([content], { type: 'text/markdown' });
                            const url = window.URL.createObjectURL(blob);
                            const a = document.createElement('a');
                            a.href = url;
                            a.download = `${currentBook.title.replace(/\s+/g, '_')}.md`;
                            a.click();
                            window.URL.revokeObjectURL(url);
                          }}
                        >
                          Download
                        </Button>
                        <Button
                          variant="outlined"
                          startIcon={<Share />}
                          onClick={() => {
                            const text = `Check out my AI-generated book: "${currentBook.title}"`;
                            if (navigator.share) {
                              navigator.share({ title: currentBook.title, text });
                            } else {
                              navigator.clipboard.writeText(text);
                              setSuccess('Book info copied to clipboard!');
                            }
                          }}
                        >
                          Share
                        </Button>
                      </Box>
                    </Box>
                  )}
                </StepContent>
              </Step>
            </Stepper>
          </Paper>
        </Grid>

        {/* Sidebar */}
        <Grid item xs={12} md={4}>
          <Paper sx={{ p: 3, mb: 2 }}>
            <Typography variant="h6" gutterBottom>
              📖 Book Progress
            </Typography>
            <List dense>
              <ListItem>
                <ListItemText 
                  primary="Total Chapters" 
                  secondary={chapters.length} 
                />
              </ListItem>
              <ListItem>
                <ListItemText 
                  primary="Total Words" 
                  secondary={getTotalWords().toLocaleString()} 
                />
              </ListItem>
              <ListItem>
                <ListItemText 
                  primary="Estimated Pages" 
                  secondary={Math.ceil(getTotalWords() / 250)} 
                />
              </ListItem>
            </List>
          </Paper>

          <Paper sx={{ p: 3 }}>
            <Typography variant="h6" gutterBottom>
              ✍️ Writing Tips
            </Typography>
            <List dense>
              <ListItem>
                <ListItemText primary="Start with a compelling concept" />
              </ListItem>
              <ListItem>
                <ListItemText primary="Develop interesting characters" />
              </ListItem>
              <ListItem>
                <ListItemText primary="Create clear chapter outlines" />
              </ListItem>
              <ListItem>
                <ListItemText primary="Maintain consistent style" />
              </ListItem>
              <ListItem>
                <ListItemText primary="Edit and refine generated content" />
              </ListItem>
            </List>
          </Paper>
        </Grid>
      </Grid>

      {/* Book Preview Dialog */}
      {previewOpen && currentBook && (
        <BookPreview
          book={currentBook}
          onClose={() => setPreviewOpen(false)}
        />
      )}
    </Box>
  );
};

export default BookGenerator;
