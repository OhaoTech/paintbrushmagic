const express = require('express');
const path = require('path');
const app = express();
const port = 5500;

app.set('view engine', 'ejs'); // Set EJS as the templating engine
app.set('views', path.join(__dirname, 'views')); // Specify the directory where EJS templates are located

// Serve static files from the 'public' directory
app.use(express.static(path.join(__dirname, 'public')));

// Your dynamic route that renders the page with the image URL
app.get('/render', (req, res) => {
    const imageUrl = req.query.image_url || '';
    // Render 'index.ejs' passing the image URL to the template
    res.render('index', { imageUrl: imageUrl });
});

app.listen(port, () => {
    console.log(`WebGL app listening at port: ${port}`);
});
