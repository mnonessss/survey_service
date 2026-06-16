import { useEffect, useState } from "react";
import { getAccessToken } from "../api/client";

type Props = {
  src: string;
  alt: string;
  className?: string;
  onClick?: () => void;
};

export function AuthenticatedImage({ src, alt, className, onClick }: Props) {
  const [blobUrl, setBlobUrl] = useState<string | null>(null);

  useEffect(() => {
    let revoked = false;
    let objectUrl = "";

    const token = getAccessToken();
    fetch(src, {
      headers: token ? { Authorization: `Bearer ${token}` } : {},
      credentials: "include",
    })
      .then((response) => {
        if (!response.ok) throw new Error("Failed to load image");
        return response.blob();
      })
      .then((blob) => {
        objectUrl = URL.createObjectURL(blob);
        if (!revoked) setBlobUrl(objectUrl);
      })
      .catch(() => {
        if (!revoked) setBlobUrl(null);
      });

    return () => {
      revoked = true;
      if (objectUrl) URL.revokeObjectURL(objectUrl);
    };
  }, [src]);

  if (!blobUrl) return null;

  return <img src={blobUrl} alt={alt} className={className} onClick={onClick} />;
}
