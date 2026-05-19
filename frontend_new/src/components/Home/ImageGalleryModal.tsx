import React, { useState, useEffect } from 'react';
import { createPortal } from 'react-dom';
import { X, ChevronLeft, ChevronRight, Download, FileDown, Loader2 } from 'lucide-react';
import JSZip from 'jszip';

interface ImageGalleryModalProps {
  isOpen: boolean;
  onClose: () => void;
  images: string[];
  title: string;
}

export const ImageGalleryModal: React.FC<ImageGalleryModalProps> = ({
  isOpen,
  onClose,
  images,
  title
}) => {
  const [currentIndex, setCurrentIndex] = useState(0);
  const [downloading, setDownloading] = useState(false);

  // CORREÇÃO: Reseta o índice sempre que as imagens mudam (evita carrossel "preso")
  useEffect(() => {
    setCurrentIndex(0);
  }, [images]);

  if (!isOpen || !images || images.length === 0) return null;

  // Safety clamp: garante que o índice nunca ultrapasse o array
  const safeIndex = Math.min(currentIndex, images.length - 1);
  const currentImage = images[safeIndex];

  const handlePrev = (e: React.MouseEvent) => {
    e.stopPropagation();
    setCurrentIndex((prev) => (prev === 0 ? images.length - 1 : prev - 1));
  };

  const handleNext = (e: React.MouseEvent) => {
    e.stopPropagation();
    setCurrentIndex((prev) => (prev === images.length - 1 ? 0 : prev + 1));
  };

  const downloadFile = async (url: string, filename: string) => {
    try {
      // Usa o proxy local para contornar CORS e forçar o navegador a tratar como download
      const proxyUrl = `http://localhost:8000/search/proxy/image?url=${encodeURIComponent(url)}`;
      const response = await fetch(proxyUrl);
      if (!response.ok) throw new Error("Erro ao baixar");
      const blob = await response.blob();
      const blobUrl = URL.createObjectURL(blob);
      
      const link = document.createElement('a');
      link.href = blobUrl;
      link.download = filename;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      URL.revokeObjectURL(blobUrl);
    } catch (err) {
      console.error("Falha no download via proxy, tentando direto:", err);
      window.open(url, '_blank');
    }
  };

  const handleDownloadAll = async () => {
    if (downloading) return;
    setDownloading(true);
    const zip = new JSZip();

    try {
      const promises = images.map(async (url, idx) => {
        try {
          const proxyUrl = `http://localhost:8000/search/proxy/image?url=${encodeURIComponent(url)}`;
          const response = await fetch(proxyUrl);
          const blob = await response.blob();
          const ext = url.split('.').pop()?.split('?')[0] || 'jpg';
          zip.file(`${title}_${idx + 1}.${ext}`, blob);
        } catch (e) {
          console.error(`Erro ao incluir foto ${idx} no ZIP:`, e);
        }
      });

      await Promise.all(promises);
      const content = await zip.generateAsync({ type: 'blob' });
      const blobUrl = URL.createObjectURL(content);
      const link = document.createElement('a');
      link.href = blobUrl;
      link.download = `${title.replace(/\s+/g, '_')}_fotos.zip`;
      link.click();
      URL.revokeObjectURL(blobUrl);
    } catch (err) {
      console.error("Erro ao gerar ZIP na galeria:", err);
      alert("Erro ao compactar as imagens.");
    } finally {
      setDownloading(false);
    }
  };

  return createPortal(
    <div 
      className="fixed inset-0 z-[999] flex items-center justify-center bg-black/95 backdrop-blur-md transition-all px-4"
      onClick={onClose}
    >
      <div 
        className="relative max-w-6xl w-full flex flex-col items-center"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Header - Ações */}
        <div className="absolute top-[-60px] right-0 flex items-center gap-3 text-white">
          {/* Botão Baixar Todas (ZIP) */}
          {images.length > 1 && (
            <button 
              onClick={handleDownloadAll}
              disabled={downloading}
              className="px-4 py-2 bg-indigo-600 hover:bg-indigo-700 disabled:bg-indigo-800/50 rounded-full transition-all flex items-center gap-2 text-sm font-bold shadow-lg"
              title="Baixar todas as imagens em ZIP"
            >
              {downloading ? (
                <Loader2 size={18} className="animate-spin" />
              ) : (
                <FileDown size={18} />
              )}
              <span>{downloading ? 'Compactando...' : 'Baixar Todas (.ZIP)'}</span>
            </button>
          )}

          {/* Botão Baixar Atual */}
          <button 
            onClick={() => downloadFile(currentImage, `${title}_${currentIndex + 1}.jpg`)}
            className="px-4 py-2 bg-white/10 hover:bg-white/20 rounded-full transition-all flex items-center gap-2 text-sm font-medium border border-white/10"
            title="Baixar imagem atual"
          >
            <Download size={18} />
            <span className="hidden sm:inline">Baixar</span>
          </button>

          {/* Botão Fechar */}
          <button 
            onClick={onClose}
            className="p-2 ml-2 hover:bg-white/10 rounded-full transition-colors text-white/70 hover:text-white"
            title="Fechar"
          >
            <X size={28} />
          </button>
        </div>

        {/* Product Title */}
        <div className="absolute top-[-50px] left-0 text-white font-semibold text-lg max-w-[60%] truncate">
          {title}
        </div>

        {/* Main Image View */}
        <div className="relative group w-full bg-white rounded-2xl overflow-hidden shadow-2xl min-h-[300px] flex items-center justify-center">
          <img 
            src={currentImage} 
            alt={`${title} - ${currentIndex + 1}`}
            className="max-h-[65vh] w-auto object-contain transition-transform duration-300"
          />

          {/* Navigation Controls */}
          {images.length > 1 && (
            <>
              <button 
                onClick={handlePrev}
                className="absolute left-4 p-3 bg-black/20 hover:bg-black/50 text-white rounded-full transition-all opacity-0 group-hover:opacity-100 backdrop-blur-md"
              >
                <ChevronLeft size={32} />
              </button>
              <button 
                onClick={handleNext}
                className="absolute right-4 p-3 bg-black/20 hover:bg-black/50 text-white rounded-full transition-all opacity-0 group-hover:opacity-100 backdrop-blur-md"
              >
                <ChevronRight size={32} />
              </button>
            </>
          )}

          {/* Counter */}
          <div className="absolute bottom-4 left-1/2 -translate-x-1/2 px-4 py-1.5 bg-black/40 backdrop-blur-md text-white text-sm rounded-full font-medium">
            {currentIndex + 1} / {images.length}
          </div>
        </div>

        {/* Thumbnails */}
        {images.length > 1 && (
          <div className="flex gap-3 mt-6 p-2 bg-white/5 rounded-xl backdrop-blur-sm overflow-x-auto max-w-full">
            {images.map((img, idx) => (
              <button
                key={idx}
                onClick={() => setCurrentIndex(idx)}
                className={`
                  relative w-16 h-16 rounded-lg overflow-hidden border-2 transition-all shrink-0
                  ${currentIndex === idx ? 'border-primary ring-2 ring-primary/20' : 'border-transparent opacity-60 hover:opacity-100'}
                `}
              >
                <img src={img} alt={`thumb ${idx}`} className="w-full h-full object-cover" />
              </button>
            ))}
          </div>
        )}
      </div>
    </div>,
    document.body
  );
};
