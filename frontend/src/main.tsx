import React, { useEffect, useContext } from 'react'
import ReactDOM from 'react-dom/client'
import { BrowserRouter, Routes, Route } from 'react-router-dom'
import Playground from './pages/Playground'
import Introduction from './pages/Introduction'
import History from './pages/History'
import './index.css'
import { UserProvider, UserContext, getUserInfo } from './contexts/UserContext'
import { Loader2 } from 'lucide-react'
import { Separator } from '@radix-ui/react-separator'

function App() {
  const [isLoading, setIsLoading] = React.useState(true);
  const { setUserInfo } = useContext(UserContext);

  useEffect(() => {
    async function loadUser() {
      const user = await getUserInfo();
      setUserInfo(user);
      setIsLoading(false);
    }
    loadUser();
  }, []);

  if (isLoading) {
    return (
      <div className="flex items-center justify-center min-h-screen bg-background">
        <div className="px-6 py-4 rounded-lg shadow-lg bg-card text-card-foreground text-lg font-medium flex">
          <Loader2 className="h-8 w-8 animate-spin" /><Separator orientation="vertical" className='mx-2' />Loading user info...
        </div>
      </div>
    );
  }

  return (
    <Routes>
      <Route path="/" element={<Playground />} />
  
      <Route path="/introduction" element={<Introduction />} />
      <Route path="/get-started" element={<Introduction />} />
      <Route path="/general" element={<Introduction />} />
      <Route path="/history" element={<History />} />
    </Routes>
  );
}

ReactDOM.createRoot(document.getElementById('root') as HTMLElement).render(
  <React.StrictMode>
    <UserProvider>
        <BrowserRouter>
          <App />
        </BrowserRouter>
    </UserProvider>
  </React.StrictMode>
)