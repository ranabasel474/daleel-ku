import { useEffect } from 'react';

//Keeps --app-height in sync with the visible viewport so the layout shrinks
//to fit above the mobile keyboard instead of letting the browser scroll the
//page (which cuts off the header behind the keyboard on iOS/Android).
export function useViewportHeight() {
  useEffect(() => {
    const vv = window.visualViewport;

    const setHeight = () => {
      const height = vv?.height ?? window.innerHeight;
      document.documentElement.style.setProperty('--app-height', `${height}px`);
      // `behavior: 'instant'` overrides the global `scroll-behavior: smooth`
      // rule — without it this scroll animates, producing a visible lag
      // between the keyboard opening and the layout snapping into place.
      window.scrollTo({ top: 0, left: 0, behavior: 'instant' });
    };

    setHeight();
    vv?.addEventListener('resize', setHeight);
    vv?.addEventListener('scroll', setHeight);
    window.addEventListener('resize', setHeight);

    return () => {
      vv?.removeEventListener('resize', setHeight);
      vv?.removeEventListener('scroll', setHeight);
      window.removeEventListener('resize', setHeight);
    };
  }, []);
}
