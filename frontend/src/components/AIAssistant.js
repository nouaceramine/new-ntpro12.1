import { useState, useEffect, useRef } from 'react';
import axios from 'axios';
import { useLanguage } from '../contexts/LanguageContext';
import { Button } from './ui/button';
import { Input } from './ui/input';
import { Badge } from './ui/badge';
import {
  Sheet,
  SheetContent,
  SheetHeader,
  SheetTitle,
  SheetTrigger,
} from './ui/sheet';
import {
  Tabs,
  TabsContent,
  TabsList,
  TabsTrigger,
} from './ui/tabs';
import { ScrollArea } from './ui/scroll-area';
import { toast } from 'sonner';
import {
  Bot,
  Send,
  Sparkles,
  TrendingUp,
  Package,
  Users,
  FileText,
  Loader2,
  Trash2,
  RefreshCw,
  Brain,
  MessageSquare,
  ChartBar,
  Lightbulb,
  X
} from 'lucide-react';

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

export function AIAssistant({ context = 'general' }) {
  const { language, isRTL } = useLanguage();
  const [isOpen, setIsOpen] = useState(false);
  const [messages, setMessages] = useState([]);
  const [inputMessage, setInputMessage] = useState('');
  const [loading, setLoading] = useState(false);
  const [activeTab, setActiveTab] = useState('chat');
  const [analysisResult, setAnalysisResult] = useState(null);
  const [analysisLoading, setAnalysisLoading] = useState(false);
  const messagesEndRef = useRef(null);
  const sessionId = `ai_session_${context}`;

  const t = {
    ar: {
      aiAssistant: 'المساعد الذكي',
      chat: 'محادثة',
      analysis: 'تحليل',
      suggestions: 'اقتراحات',
      typeMessage: 'اكتب رسالتك...',
      send: 'إرسال',
      clearChat: 'مسح المحادثة',
      salesForecast: 'توقع المبيعات',
      restockSuggestions: 'اقتراحات التخزين',
      customerInsights: 'تحليل العملاء',
      productDescription: 'وصف المنتج',
      analyzing: 'جاري التحليل...',
      noMessages: 'ابدأ محادثة مع المساعد الذكي',
      welcomeMessage: 'مرحباً! أنا مساعدك الذكي. كيف يمكنني مساعدتك اليوم؟',
      quickActions: 'إجراءات سريعة',
      error: 'حدث خطأ',
      aiPowered: 'مدعوم بالذكاء الاصطناعي'
    },
    fr: {
      aiAssistant: 'Assistant IA',
      chat: 'Chat',
      analysis: 'Analyse',
      suggestions: 'Suggestions',
      typeMessage: 'Tapez votre message...',
      send: 'Envoyer',
      clearChat: 'Effacer le chat',
      salesForecast: 'Prévision des ventes',
      restockSuggestions: 'Suggestions de réapprovisionnement',
      customerInsights: 'Analyse clients',
      productDescription: 'Description produit',
      analyzing: 'Analyse en cours...',
      noMessages: 'Démarrez une conversation avec l\'assistant IA',
      welcomeMessage: 'Bonjour! Je suis votre assistant IA. Comment puis-je vous aider?',
      quickActions: 'Actions rapides',
      error: 'Une erreur s\'est produite',
      aiPowered: 'Propulsé par l\'IA'
    }
  };

  const texts = t[language] || t.ar;

  useEffect(() => {
    if (isOpen) {
      loadChatHistory();
    }
  }, [isOpen]);

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  const loadChatHistory = async () => {
    try {
      const token = localStorage.getItem('token');
      const response = await axios.get(`${API}/ai/chat-history/${sessionId}`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      if (response.data.messages.length > 0) {
        setMessages(response.data.messages);
      } else {
        // Add welcome message
        setMessages([{
          role: 'assistant',
          content: texts.welcomeMessage,
          timestamp: new Date().toISOString()
        }]);
      }
    } catch (error) {
      console.error('Error loading chat history:', error);
    }
  };

  const sendMessage = async () => {
    if (!inputMessage.trim() || loading) return;

    const userMessage = {
      role: 'user',
      content: inputMessage,
      timestamp: new Date().toISOString()
    };

    setMessages(prev => [...prev, userMessage]);
    setInputMessage('');
    setLoading(true);

    try {
      const token = localStorage.getItem('token');
      const response = await axios.post(`${API}/ai/chat`, {
        message: inputMessage,
        session_id: sessionId,
        context: context
      }, {
        headers: { Authorization: `Bearer ${token}` }
      });

      setMessages(prev => [...prev, {
        role: 'assistant',
        content: response.data.response,
        timestamp: new Date().toISOString()
      }]);
    } catch (error) {
      console.error('Error sending message:', error);
      toast.error(texts.error);
      setMessages(prev => [...prev, {
        role: 'assistant',
        content: language === 'ar' ? 'عذراً، حدث خطأ. يرجى المحاولة مرة أخرى.' : 'Désolé, une erreur s\'est produite. Veuillez réessayer.',
        timestamp: new Date().toISOString()
      }]);
    } finally {
      setLoading(false);
    }
  };

  const clearChat = async () => {
    try {
      const token = localStorage.getItem('token');
      await axios.delete(`${API}/ai/chat-history/${sessionId}`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setMessages([{
        role: 'assistant',
        content: texts.welcomeMessage,
        timestamp: new Date().toISOString()
      }]);
      toast.success(language === 'ar' ? 'تم مسح المحادثة' : 'Chat effacé');
    } catch (error) {
      console.error('Error clearing chat:', error);
    }
  };

  const runAnalysis = async (analysisType) => {
    setAnalysisLoading(true);
    setAnalysisResult(null);

    try {
      const token = localStorage.getItem('token');
      const response = await axios.post(`${API}/ai/analyze`, {
        analysis_type: analysisType
      }, {
        headers: { Authorization: `Bearer ${token}` }
      });

      setAnalysisResult({
        type: analysisType,
        content: response.data.analysis
      });
    } catch (error) {
      console.error('Error running analysis:', error);
      toast.error(texts.error);
    } finally {
      setAnalysisLoading(false);
    }
  };

  const handleKeyPress = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  };

  const getContextIcon = () => {
    switch (context) {
      case 'sales': return <TrendingUp className="h-4 w-4" />;
      case 'inventory': return <Package className="h-4 w-4" />;
      case 'customers': return <Users className="h-4 w-4" />;
      case 'reports': return <FileText className="h-4 w-4" />;
      default: return <Bot className="h-4 w-4" />;
    }
  };

  return (
    <Sheet open={isOpen} onOpenChange={setIsOpen}>
      <SheetTrigger asChild>
        <Button
          variant="outline"
          size="icon"
          className="fixed bottom-6 end-6 h-14 w-14 rounded-full shadow-lg bg-gradient-to-br from-violet-500 to-purple-600 hover:from-violet-600 hover:to-purple-700 text-white border-0 z-50"
          data-testid="ai-assistant-trigger"
        >
          <Sparkles className="h-6 w-6" />
        </Button>
      </SheetTrigger>
      <SheetContent 
        side={isRTL ? "left" : "right"} 
        className="w-full sm:w-[450px] p-0 flex flex-col"
        data-testid="ai-assistant-panel"
      >
        <SheetHeader className="p-4 border-b bg-gradient-to-r from-violet-500 to-purple-600 text-white">
          <SheetTitle className="flex items-center gap-2 text-white">
            <Brain className="h-5 w-5" />
            {texts.aiAssistant}
            <Badge variant="secondary" className="ms-2 bg-white/20 text-white text-xs">
              {texts.aiPowered}
            </Badge>
          </SheetTitle>
        </SheetHeader>

        <Tabs value={activeTab} onValueChange={setActiveTab} className="flex-1 flex flex-col">
          <TabsList className="grid w-full grid-cols-2 p-1 m-2">
            <TabsTrigger value="chat" className="gap-2">
              <MessageSquare className="h-4 w-4" />
              {texts.chat}
            </TabsTrigger>
            <TabsTrigger value="analysis" className="gap-2">
              <ChartBar className="h-4 w-4" />
              {texts.analysis}
            </TabsTrigger>
          </TabsList>

          {/* Chat Tab */}
          <TabsContent value="chat" className="flex-1 flex flex-col p-0 m-0">
            <ScrollArea className="flex-1 p-4">
              <div className="space-y-4">
                {messages.map((msg, idx) => (
                  <div
                    key={idx}
                    className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}
                  >
                    <div
                      className={`max-w-[85%] rounded-2xl px-4 py-2.5 ${
                        msg.role === 'user'
                          ? 'bg-gradient-to-br from-violet-500 to-purple-600 text-white'
                          : 'bg-muted'
                      }`}
                    >
                      {msg.role === 'assistant' && (
                        <div className="flex items-center gap-1.5 mb-1.5 text-xs text-muted-foreground">
                          <Bot className="h-3 w-3" />
                          AI
                        </div>
                      )}
                      <p className="text-sm whitespace-pre-wrap leading-relaxed">{msg.content}</p>
                    </div>
                  </div>
                ))}
                {loading && (
                  <div className="flex justify-start">
                    <div className="bg-muted rounded-2xl px-4 py-3">
                      <Loader2 className="h-5 w-5 animate-spin text-violet-500" />
                    </div>
                  </div>
                )}
                <div ref={messagesEndRef} />
              </div>
            </ScrollArea>

            {/* Quick Actions */}
            <div className="p-3 border-t bg-muted/30">
              <p className="text-xs text-muted-foreground mb-2">{texts.quickActions}</p>
              <div className="flex flex-wrap gap-1.5">
                <Button
                  variant="outline"
                  size="sm"
                  className="text-xs h-7"
                  onClick={() => setInputMessage(language === 'ar' ? 'ما هي أفضل المنتجات مبيعاً؟' : 'Quels sont les meilleurs produits?')}
                >
                  <TrendingUp className="h-3 w-3 me-1" />
                  {language === 'ar' ? 'أفضل المنتجات' : 'Top produits'}
                </Button>
                <Button
                  variant="outline"
                  size="sm"
                  className="text-xs h-7"
                  onClick={() => setInputMessage(language === 'ar' ? 'كيف يمكنني زيادة المبيعات؟' : 'Comment augmenter les ventes?')}
                >
                  <Lightbulb className="h-3 w-3 me-1" />
                  {language === 'ar' ? 'نصائح' : 'Conseils'}
                </Button>
                <Button
                  variant="outline"
                  size="sm"
                  className="text-xs h-7"
                  onClick={() => setInputMessage(language === 'ar' ? 'ما المنتجات التي تحتاج إعادة تخزين؟' : 'Quels produits faut-il réapprovisionner?')}
                >
                  <Package className="h-3 w-3 me-1" />
                  {language === 'ar' ? 'المخزون' : 'Stock'}
                </Button>
              </div>
            </div>

            {/* Input Area */}
            <div className="p-3 border-t">
              <div className="flex gap-2">
                <Button
                  variant="ghost"
                  size="icon"
                  className="shrink-0 text-muted-foreground hover:text-destructive"
                  onClick={clearChat}
                  title={texts.clearChat}
                >
                  <Trash2 className="h-4 w-4" />
                </Button>
                <Input
                  value={inputMessage}
                  onChange={(e) => setInputMessage(e.target.value)}
                  onKeyPress={handleKeyPress}
                  placeholder={texts.typeMessage}
                  disabled={loading}
                  className="flex-1"
                  data-testid="ai-chat-input"
                />
                <Button
                  onClick={sendMessage}
                  disabled={loading || !inputMessage.trim()}
                  className="shrink-0 bg-gradient-to-r from-violet-500 to-purple-600 hover:from-violet-600 hover:to-purple-700"
                  data-testid="ai-send-btn"
                >
                  {loading ? (
                    <Loader2 className="h-4 w-4 animate-spin" />
                  ) : (
                    <Send className="h-4 w-4" />
                  )}
                </Button>
              </div>
            </div>
          </TabsContent>

          {/* Analysis Tab */}
          <TabsContent value="analysis" className="flex-1 p-4 space-y-4 m-0">
            <div className="grid grid-cols-2 gap-3">
              <Button
                variant="outline"
                className="h-auto py-4 flex-col gap-2 hover:border-violet-300 hover:bg-violet-50"
                onClick={() => runAnalysis('sales_forecast')}
                disabled={analysisLoading}
              >
                <TrendingUp className="h-6 w-6 text-violet-500" />
                <span className="text-xs">{texts.salesForecast}</span>
              </Button>
              <Button
                variant="outline"
                className="h-auto py-4 flex-col gap-2 hover:border-green-300 hover:bg-green-50"
                onClick={() => runAnalysis('restock')}
                disabled={analysisLoading}
              >
                <Package className="h-6 w-6 text-green-500" />
                <span className="text-xs">{texts.restockSuggestions}</span>
              </Button>
              <Button
                variant="outline"
                className="h-auto py-4 flex-col gap-2 hover:border-blue-300 hover:bg-blue-50"
                onClick={() => runAnalysis('customer_insights')}
                disabled={analysisLoading}
              >
                <Users className="h-6 w-6 text-blue-500" />
                <span className="text-xs">{texts.customerInsights}</span>
              </Button>
              <Button
                variant="outline"
                className="h-auto py-4 flex-col gap-2 hover:border-amber-300 hover:bg-amber-50"
                onClick={() => runAnalysis('product_description')}
                disabled={analysisLoading}
              >
                <FileText className="h-6 w-6 text-amber-500" />
                <span className="text-xs">{texts.productDescription}</span>
              </Button>
            </div>

            {/* Analysis Result */}
            {analysisLoading && (
              <div className="flex items-center justify-center py-12">
                <div className="text-center space-y-3">
                  <Loader2 className="h-10 w-10 animate-spin text-violet-500 mx-auto" />
                  <p className="text-sm text-muted-foreground">{texts.analyzing}</p>
                </div>
              </div>
            )}

            {analysisResult && !analysisLoading && (
              <div className="mt-4 p-4 bg-muted rounded-xl">
                <div className="flex items-center gap-2 mb-3">
                  <Sparkles className="h-4 w-4 text-violet-500" />
                  <span className="font-medium text-sm">
                    {analysisResult.type === 'sales_forecast' && texts.salesForecast}
                    {analysisResult.type === 'restock' && texts.restockSuggestions}
                    {analysisResult.type === 'customer_insights' && texts.customerInsights}
                    {analysisResult.type === 'product_description' && texts.productDescription}
                  </span>
                </div>
                <div className="text-sm whitespace-pre-wrap leading-relaxed">
                  {analysisResult.content}
                </div>
              </div>
            )}
          </TabsContent>
        </Tabs>
      </SheetContent>
    </Sheet>
  );
}

export default AIAssistant;
