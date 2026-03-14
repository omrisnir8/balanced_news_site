import React from 'react';
import styles from '../styles/BiasBadge.module.css';

interface BiasBadgeProps {
    type: 'location' | 'orientation' | 'bias';
    text: string;
}

export default function BiasBadge({ type, text }: BiasBadgeProps) {
    return (
        <span className={`${styles.badge} ${styles[type]}`}>
            {text}
        </span>
    );
}
