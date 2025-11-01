# LN-Manager

A modern web application for managing your light novel collection with automatic metadata fetching, release tracking, and a beautiful calendar interface.

## Features

- **Organize Your Collection**: Keep track of all your light novels with series groups and collections
- **Release Calendar**: Never miss a release with month and week calendar views
- **Metadata Handling**: Fetch series/book information, cover images, and release dates from various sources automatically using plugins.

## Screenshots

*[Screenshots coming soon]*

## Installation & Setup

### Requirements

- **Python 3.9 or higher**
- **Node.js 18 or higher**
- **pip** (Python package manager)
- **npm** or **yarn** (Node package manager)

### Quick Start

1. **Clone the repository**

   ```bash
   git clone <repository-url>
   cd ln-auto-v2
   ```

2. **Install Backend Dependencies**

   ```bash
   cd backend
   pip install -r requirements.txt
   ```

3. **Install Frontend Dependencies**

   ```bash
   cd ../frontend
   npm install
   ```

4. **Start the Backend Server**

   Open a terminal and run:

   ```bash
   cd backend
   fastapi run
   ```

   The backend will start at `http://localhost:8000`

5. **Start the Frontend**

   Open a **new terminal** and run:

   ```bash
   cd frontend
   yarn build
   ```

   The web interface will open at `http://localhost:5173`

6. **Start Using LN-Auto!**

   - Open your browser to `http://localhost:5173`
   - Click search bar to open the search palette
   - Search for a light novel series and add it to your library
   - View your collection, check the release calendar, and enjoy!

## Usage Tips

- **Quick Search**: Press `Ctrl+K` (Windows/Linux) or `Cmd+K` (Mac) anywhere to open the search palette
- **Add Series**: Search for a series, click on a result, then click "Add to Library"
- **Calendar View**: Navigate to the Calendar page to see all upcoming releases
- **Automatic Updates**: Series metadata automatically refreshes every hour
- **Notifications**: Check the notifications page to see history of all updates

## Default Plugins

Metadata sources:

- **RanobeDB** - Light novel database with English and Japanese titles, cover images, and release dates

## TODOs

- [ ] Dockerize application.
- [ ] Add Alembic Migrations
- [ ] Register Custom Plugin API routes.
- [ ] Add proper dependancy management for plugins.
- [ ] Add loading overlays to images/cards/tables everywhere.
- [ ] Make series download status include percentages.
- [ ] Add new schedular to check and notify if it is release day for any releases in the database.
- [ ] Create filter options for library page and calendar page.
- [ ] Add config options across application
- [ ] Make Logo

### Known Issues

- [ ] Unclear if restart backend endpoint works in production.
- [ ] Spotlight search does not repopulate the "existing series" until force refresh - ctrl-shift-r

## Contributing

Contributions are welcome! There are many ways to help:

- **Report Bugs**: Found an issue? Open a bug report with details about what went wrong
- **Pull Request**: Pull requests are welcome!
- **Improve Documentation**: Help make our docs clearer and more comprehensive
- **Enhance UI/UX**: Improve the design, add features, or fix visual issues
- **Write Tests**: Help improve code quality and reliability

### For Developers

If you're interested in contributing code:

1. **Fork the repository** and clone it locally
2. **Read the documentation**:
   - [Backend Developer Guide](backend/ReadMe.md) - API development and plugin creation
   - [Frontend Developer Guide](frontend/ReadMe.md) - UI components and features
3. **Pick an issue** or create a new one to discuss your changes
4. **Make your changes** and test thoroughly
5. **Submit a pull request** with a clear description

### Plugin Development

Creating plugins is one of the best ways to extend LN-Auto! Check out:

- The [Backend README](backend/ReadMe.md) for detailed plugin development guide
- The `backend/plugins/RanobeDB/` directory for a working example

## Acknowledgments

- [RanobeDB](https://ranobedb.org/) for providing comprehensive light novel metadata
- [Mantine](https://mantine.dev/) for the beautiful UI component library
- [FastAPI](https://fastapi.tiangolo.com/) for the excellent Python web framework

---

**Status**: Active Development

This project is under active development. Expect frequent updates and new features!
