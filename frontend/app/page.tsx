"use client";

import { useEffect, useState, useRef } from 'react';
import ArticleCard, { ClusterProps } from '@/components/ArticleCard';
import { RefreshCw, Search, Activity } from 'lucide-react';

const DEFAULT_CATEGORIES = ["All", "General News", "Economics", "Culture", "Technology", "Geopolitics", "Sport", "Science", "Health", "Entertainment"];
const API_BASE = process.env.NEXT_PUBLIC_API_BASE || "http://10.100.102.13:8000/api";

export default function Home() {
  const [feed, setFeed] = useState<ClusterProps[]>([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [statusMessage, setStatusMessage] = useState("");
  const [activeCategory, setActiveCategory] = useState("All");
  const [categories, setCategories] = useState<string[]>(DEFAULT_CATEGORIES);
  const [editMode, setEditMode] = useState(false);
  const [language, setLanguage] = useState<"en" | "he" | "native">("en");
  const [startY, setStartY] = useState(0);
  const pollInterval = useRef<NodeJS.Timeout | null>(null);

  // Load custom category order
  useEffect(() => {
    const saved = localStorage.getItem('custom_categories');
    if (saved) {
      try {
        const parsed = JSON.parse(saved);
        if (Array.isArray(parsed) && parsed.length > 0) {
          // Merge with any new default categories (in case we added some)
          const merged = [...new Set([...parsed, ...DEFAULT_CATEGORIES])];
          setCategories(merged);
        }
      } catch (e) {
        console.error("Failed to parse categories", e);
      }
    }
  }, []);

  const saveCategories = (newList: string[]) => {
    setCategories(newList);
    localStorage.setItem('custom_categories', JSON.stringify(newList));
  };

  const moveCategory = (index: number, direction: 'left' | 'right') => {
    const newList = [...categories];
    const newIdx = direction === 'left' ? index - 1 : index + 1;
    if (newIdx < 0 || newIdx >= newList.length) return;
    [newList[index], newList[newIdx]] = [newList[newIdx], newList[index]];
    saveCategories(newList);
  };

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
          <div className="header-actions">
            <button
              onClick={() => setEditMode(!editMode)}
              className="edit-btn"
              style={{ color: editMode ? 'var(--accent-blue)' : 'var(--text-secondary)' }}
            >
              {editMode ? 'Done' : 'Edit'}
            </button>
            <button
              onClick={handleRefresh}
              disabled={refreshing}
              className="refresh-icon"
            >
              <RefreshCw
                size={22}
                strokeWidth={2.5}
                className={refreshing ? "animate-spin" : ""}
              />
            </button>
          </div>
        </div>

        <nav className="categories-container">
          {categories.map((cat, idx) => (
            <div key={cat} className="category-item">
              <button
                className={`category-tab ${activeCategory === cat ? 'active' : ''}`}
                onClick={() => !editMode && setActiveCategory(cat)}
              >
                {cat}
              </button>
              {editMode && (
                <div className="reorder-tools">
                  <button onClick={() => moveCategory(idx, 'left')} disabled={idx === 0}>←</button>
                  <button onClick={() => moveCategory(idx, 'right')} disabled={idx === categories.length - 1}>→</button>
                </div>
              )}
            </div>
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
          <div className="empty-state">
            <div className="spinner" />
            <p>Updating your perspective...</p>
          </div>
        ) : feed.length > 0 ? (
          feed.map(cluster => (
            <ArticleCard key={cluster.id} cluster={cluster} language={language} />
          ))
        ) : (
          <div className="empty-state">
            <p>No news found for this category.</p>
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

         .header-actions {
             display: flex;
             align-items: center;
             gap: 16px;
         }

         .edit-btn {
             font-size: 0.95rem;
             font-weight: 600;
             transition: all 0.2s;
         }

         .category-item {
             display: flex;
             flex-direction: column;
             align-items: center;
             gap: 4px;
         }

         .reorder-tools {
             display: flex;
             gap: 8px;
             font-size: 0.7rem;
             background: rgba(0,0,0,0.05);
             border-radius: 4px;
             padding: 2px 4px;
         }

         .reorder-tools button {
             opacity: 0.6;
         }
         .reorder-tools button:disabled {
             opacity: 0.2;
         }

         .empty-state {
             text-align: center;
             padding: 120px 40px;
             color: var(--text-secondary);
         }

         .spinner {
             width: 24px;
             height: 24px;
             border: 2px solid rgba(0,0,0,0.1);
             border-top: 2px solid var(--accent-blue);
             border-radius: 50%;
             margin: 0 auto 16px;
             animation: spin 0.8s linear infinite;
         }
      `}</style>
    </div>
  );
}
