import React, { useState, useEffect } from 'react';

const ScrambleText = ({ text, className = "", duration = 1000 }) => {
    const [display, setDisplay] = useState(text);
    const chars = "ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789@#$%&*";

    useEffect(() => {
        let iterations = 0;
        const interval = setInterval(() => {
            setDisplay(
                String(text).split("")
                    .map((char, index) => {
                        if (index < iterations) return char;
                        return chars[Math.floor(Math.random() * chars.length)];
                    })
                    .join("")
            );

            if (iterations >= String(text).length) clearInterval(interval);
            iterations += 1 / 3;
        }, 30);

        return () => clearInterval(interval);
    }, [text]);

    return <span className={className}>{display}</span>;
};

export default ScrambleText;
