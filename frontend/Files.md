REM asigură-te că proiectul Next.js există deja (create-next-app)
mkdir src\app
type nul > src\app\layout.js
type nul > src\app\globals.css
type nul > src\app\page.js

mkdir src\app\(auth)\login
mkdir src\app\(auth)\register
type nul > src\app\(auth)\login\page.js
type nul > src\app\(auth)\register\page.js

mkdir src\app\chat
type nul > src\app\chat\page.js

mkdir src\app\dashboard
type nul > src\app\dashboard\page.js

REM Auth
mkdir src\app\api\auth\login
mkdir src\app\api\auth\register
mkdir src\app\api\auth\me
type nul > src\app\api\auth\login\route.js
type nul > src\app\api\auth\register\route.js
type nul > src\app\api\auth\me\route.js

REM Chat
mkdir src\app\api\chat
type nul > src\app\api\chat\route.js

REM History (listare conversații + mesaje)
mkdir src\app\api\history
type nul > src\app\api\history\route.js

REM Favorites
mkdir src\app\api\favorites
type nul > src\app\api\favorites\route.js

mkdir src\components
type nul > src\components\ChatInput.jsx
type nul > src\components\ChatMessage.jsx
type nul > src\components\HistorySidebar.jsx
type nul > src\components\Navbar.jsx
type nul > src\components\Protected.jsx

mkdir src\lib
type nul > src\lib\api.js
type nul > src\lib\auth.js

mkdir src\store
type nul > src\store\chatStore.js

type nul > middleware.js

mkdir public\icons
type nul > public\icons\book.svg
