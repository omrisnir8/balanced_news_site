"use client";

import { useEffect, useState, useRef } from 'react';
import ArticleCard, { ClusterProps } from '@/components/ArticleCard';
import { RefreshCw, Search, Activity } from 'lucide-react';

const CATEGORIES = ["All", "General News", "Economics", "Culture", "Technology", "Geopolitics"];
const API_BASE = process.env.NEXT_PUBLIC_API_BASE || "http://10.100.102.13:8000/api";

export default function Home() {
  const [feed, setFeed] = useState<ClusterProps[]>([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [statusMessage, setStatusMessage] = useState("");
  const [activeCategory, setActiveCategory] = useState("All");
  const [language, setLanguage] = useState<"en" | "he" | "native">("en");
  const [startY, setStartY] = useState(0);
  const pollInterval = useRef<NodeJS.Timeout | null>(null);

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

  const pollStatus = async () => {
    try {
      const res = await fetch(`${API_BASE}/status`);
      const data = await res.json();

      if (data.status === "processing") {
        setStatusMessage(data.message);
        setRefreshing(true);
      } else {
        setStatusMessage("");
        setRefreshing(false);
        if (pollInterval.current) {
          clearInterval(pollInterval.current);
          pollInterval.current = null;
        }
        fetchFeed(activeCategory);
      }
    } catch (err) {
      console.error("Polling error:", err);
    }
  };

  const handleRefresh = async () => {
    if (refreshing) return;
    setRefreshing(true);
    setStatusMessage("Starting refresh...");
    try {
      const res = await fetch(`${API_BASE}/refresh`, { method: "POST" });
      const data = await res.json();

      if (data.status === "processing") {
        // Start polling
        if (!pollInterval.current) {
          pollInterval.current = setInterval(pollStatus, 3000);
        }
      }
    } catch (err) {
      console.error("Failed to refresh feed:", err);
      setRefreshing(false);
      setStatusMessage("");
    }
  };

  useEffect(() => {
    fetchFeed(activeCategory);
    // Check initial status in case a refresh is already running
    pollStatus();
    return () => {
      if (pollInterval.current) clearInterval(pollInterval.current);
    };
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
          <button
            onClick={handleRefresh}
            disabled={refreshing}
            className="refresh-icon"
          >
            <RefreshCw
              size={24}
              className={refreshing ? "animate-spin" : ""}
            />
          </button>
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
        {statusMessage && (
          <div className="status-indicator">
            <Activity size={14} className="animate-pulse" />
            <span>{statusMessage}</span>
          </div>
        )}

        {loading && !refreshing ? (
          <div style={{ textAlign: 'center', padding: '100px 40px', color: 'var(--text-secondary)', fontSize: '0.9rem' }}>
            Updating your perspective...
          </div>
        ) : feed.length > 0 ? (
          feed.map(cluster => (
            <ArticleCard key={cluster.id} cluster={cluster} language={language} />
          ))
        ) : (
          <div style={{ textAlign: 'center', padding: '100px 40px', color: 'var(--text-secondary)' }}>
            No news found for this category.
          </div>
        )}
      </main>

      <style jsx>{`
         .language-toggle {
             display: none;
         }
         
         @keyframes pulse {
           0%, 100% { opacity: 1; }
           50% { opacity: 0.4; }
         }
         .animate-pulse {
           animation: pulse 2s cubic-bezier(0.4, 0, 0.2, 1) infinite;
         }
      `}</style>
    </div>
  );
}
