"use client";

import { useEffect, useState } from 'react';
import ArticleCard, { ClusterProps } from '@/components/ArticleCard';
import { RefreshCw, Search } from 'lucide-react';

const CATEGORIES = ["All", "General News", "Economics", "Culture", "Technology", "Geopolitics"];
const API_BASE = process.env.NEXT_PUBLIC_API_BASE || "http://10.100.102.13:8000/api";

export default function Home() {
  const [feed, setFeed] = useState<ClusterProps[]>([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [activeCategory, setActiveCategory] = useState("All");
  const [language, setLanguage] = useState<"en" | "he" | "native">("en");
  const [startY, setStartY] = useState(0);

  const fetchFeed = async (category = "All") => {
    setLoading(true);
    try {
      const url = category === "All" ? `${API_BASE}/feed` : `${API_BASE}/feed?category=${encodeURIComponent(category)}`;
      const res = await fetch(url);
      const data = await res.json();
      setFeed(data);
    } catch (err) {
      console.error("Failed to fetch feed:", err);
    } finally {
      setLoading(false);
    }
  };

  const handleRefresh = async () => {
    setRefreshing(true);
    try {
      await fetch(`${API_BASE}/refresh`, { method: "POST" });
      await fetchFeed(activeCategory);
    } catch (err) {
      console.error("Failed to refresh feed:", err);
    } finally {
      setRefreshing(false);
    }
  };

  useEffect(() => {
    fetchFeed(activeCategory);
  }, [activeCategory]);

  const handleTouchStart = (e: React.TouchEvent) => {
    if (window.scrollY === 0) {
      setStartY(e.touches[0].clientY);
    }
  };

  const handleTouchEnd = (e: React.TouchEvent) => {
    if (startY === 0) return;
    const endY = e.changedTouches[0].clientY;
    if (endY - startY > 100 && window.scrollY === 0) {
      handleRefresh();
    }
    setStartY(0);
  };

  return (
    <div className="app-container">
      <header className="header">
        <div className="header-top">
          <h1 className="logo">Balanced News</h1>
          <div className="language-toggle">
            <button className={language === 'en' ? 'active' : ''} onClick={() => setLanguage('en')}>EN</button>
            <button className={language === 'he' ? 'active' : ''} onClick={() => setLanguage('he')}>HE</button>
            <button className={language === 'native' ? 'active' : ''} onClick={() => setLanguage('native')}>NAT</button>
          </div>
        </div>

        <nav className="categories-container">
          {CATEGORIES.map(cat => (
            <button
              key={cat}
              className={`category-tab ${activeCategory === cat ? 'active' : ''}`}
              onClick={() => setActiveCategory(cat)}
            >
              {cat}
            </button>
          ))}
        </nav>
      </header>

      <main
        className="feed-container"
        onTouchStart={handleTouchStart}
        onTouchEnd={handleTouchEnd}
      >
        <button
          className="refresh-button"
          onClick={handleRefresh}
          disabled={refreshing}
        >
          <RefreshCw
            size={16}
            className={refreshing ? "animate-spin" : ""}
            style={{ animation: refreshing ? "spin 1s linear infinite" : "none" }}
          />
          {refreshing ? "Updating Feed..." : "Refresh Feed"}
        </button>

        {loading ? (
          <div style={{ textAlign: 'center', padding: '40px', color: 'var(--text-secondary)' }}>
            Loading latest perspectives...
          </div>
        ) : feed.length > 0 ? (
          feed.map(cluster => (
            <ArticleCard key={cluster.id} cluster={cluster} language={language} />
          ))
        ) : (
          <div style={{ textAlign: 'center', padding: '40px', color: 'var(--text-secondary)' }}>
            No news found for this category. Click Refresh to fetch updates.
          </div>
        )}
      </main>

      <style jsx>{`
         @keyframes spin {
           from { transform: rotate(0deg); }
           to { transform: rotate(360deg); }
         }
         
         .language-toggle {
             display: flex;
             background: rgba(255, 255, 255, 0.1);
             border-radius: var(--radius-sm);
             padding: 2px;
             gap: 2px;
         }
         .language-toggle button {
             background: transparent;
             border: none;
             color: var(--text-secondary);
             padding: 6px 10px;
             font-size: 0.8rem;
             font-weight: 700;
             cursor: pointer;
             border-radius: 4px;
             transition: all 0.2s;
         }
         .language-toggle button.active {
             background: var(--accent-blue);
             color: white;
         }
      `}</style>
    </div>
  );
}
