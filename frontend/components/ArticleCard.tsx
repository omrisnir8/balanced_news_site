import React from 'react';
import styles from '../styles/ArticleCard.module.css';
import BiasBadge from './BiasBadge';
import { ExternalLink, Clock } from 'lucide-react';

export interface SourceArticle {
    source_name: string;
    location: string;
    political_orientation: string;
    known_bias: string;
    url: string;
    published_at?: string;
    titles: {
        native: string;
        en: string;
        he: string;
    };
    bias_warnings: {
        en: string;
        he: string;
    };
}

export interface ClusterProps {
    id: number;
    titles: {
        en: string;
        he: string;
    };
    summaries: {
        en: string;
        he: string;
    };
    timestamp: string;
    category: string;
    sources: SourceArticle[];
}

function timeAgo(dateString: string) {
    if (!dateString) return '';
    const date = new Date(dateString);
    const now = new Date();
    const seconds = Math.floor((now.getTime() - date.getTime()) / 1000);

    let interval = seconds / 31536000;
    if (interval > 1) return Math.floor(interval) + " years ago";
    interval = seconds / 2592000;
    if (interval > 1) return Math.floor(interval) + " months ago";
    interval = seconds / 86400;
    if (interval > 1) return Math.floor(interval) + " days ago";
    interval = seconds / 3600;
    if (interval > 1) return Math.floor(interval) + " hours ago";
    interval = seconds / 60;
    if (interval > 1) return Math.floor(interval) + " minutes ago";
    return Math.floor(seconds) + " seconds ago";
}

function formatExactHour(dateString?: string) {
    if (!dateString) return '';
    try {
        const date = new Date(dateString);
        return date.toLocaleTimeString('en-IL', { hour: '2-digit', minute: '2-digit', timeZone: 'Asia/Jerusalem' });
    } catch {
        return '';
    }
}

export default function ArticleCard({ cluster, language }: { cluster: ClusterProps, language: "en" | "he" | "native" }) {
    const isRtl = language === 'he' || (language === 'native' && cluster.titles.he);
    const displayTitle = (language === 'en') ? cluster.titles.en : cluster.titles.he;
    const displaySummary = (language === 'en') ? cluster.summaries.en : cluster.summaries.he;

    return (
        <article className={styles.card} dir={isRtl ? 'rtl' : 'ltr'}>
            <div className={styles.header}>
                <div className={styles.meta}>
                    <span className={styles.category}>{cluster.category}</span>
                    <span className={styles.timestamp}>
                        <Clock size={12} className={styles.icon} />
                        {timeAgo(cluster.timestamp) || 'Just now'}
                    </span>
                </div>
                <h2 className={styles.title}>{displayTitle}</h2>
            </div>

            <div className={styles.summaryContainer}>
                <div className={styles.summaryLabel}>{language === 'he' ? 'סיכום השוואתי' : 'Comparative Summary'}</div>
                <p className={styles.summary}>{displaySummary}</p>
            </div>

            <div className={styles.sourcesSection}>
                <h3 className={styles.sourcesLabel}>{language === 'he' ? 'מקורות' : 'Sources'} ({cluster.sources.length})</h3>
                <div className={styles.sourcesList}>
                    {cluster.sources.map((source, idx) => {
                        const sourceTitle = language === 'native' ? source.titles.native : language === 'he' ? source.titles.he : source.titles.en;
                        const sourceBias = language === 'he' ? source.bias_warnings.he : source.bias_warnings.en;

                        return (
                            <a
                                key={idx}
                                href={source.url}
                                target="_blank"
                                rel="noopener noreferrer"
                                className={styles.sourceItem}
                            >
                                <div className={styles.sourceMain}>
                                    <span className={styles.sourceName}>
                                        {source.source_name}
                                        {source.published_at && <span style={{ opacity: 0.6, fontWeight: 400, margin: "0 6px" }}>• {formatExactHour(source.published_at)}</span>}
                                    </span>
                                    <ExternalLink size={14} className={styles.linkIcon} />
                                </div>

                                <h4 style={{ margin: "4px 0 8px 0", fontSize: "0.95rem", fontWeight: 500, color: "var(--text-primary)" }}>
                                    {sourceTitle}
                                </h4>

                                <div className={styles.badges}>
                                    <BiasBadge type="location" text={source.location} />
                                    <BiasBadge type="orientation" text={source.political_orientation} />
                                    <BiasBadge type="bias" text={source.known_bias} />
                                </div>
                                {sourceBias && (
                                    <div className={styles.biasWarning}>
                                        <span className={styles.warningLabel}>{language === 'he' ? 'הערת מנתח:' : 'Analyzer Note:'}</span>
                                        {sourceBias}
                                    </div>
                                )}
                            </a>
                        );
                    })}
                </div>
            </div>
        </article>
    );
}
