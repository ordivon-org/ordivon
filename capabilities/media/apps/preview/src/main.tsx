import {StrictMode} from 'react';
import {createRoot} from 'react-dom/client';
import '@ordivon/identity/tokens.css';
import './styles.css';
import {App} from './app.tsx';

const root = document.getElementById('root');
if (!root) throw new Error('missing #root');

createRoot(root).render(
  <StrictMode>
    <App />
  </StrictMode>,
);
