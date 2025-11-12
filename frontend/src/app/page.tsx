/**
 * Home page - redirects to admin dashboard.
 * This is the entry point for the application.
 */

import { redirect } from 'next/navigation';

export default function HomePage() {
  redirect('/admin');
}

