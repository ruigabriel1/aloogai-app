import React, { useState } from 'react';
import { View, Text, StyleSheet, ScrollView, Alert, KeyboardAvoidingView, Platform, Image, TouchableOpacity, ActivityIndicator } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { useNavigation } from '@react-navigation/native';
import { useTheme } from '../../theme';
import { TextStyles, FontFamily } from '../../theme/typography';
import { Spacing, BorderRadius } from '../../theme/spacing';
import { BrandColors } from '../../theme/colors';
import { Button } from '../../components/ui/Button';
import { Input } from '../../components/ui/Input';
import { useMutation, useQueryClient, useQuery } from '@tanstack/react-query';
import { criarItem, buscarCategorias } from '../../api/catalog';
import { useLocation } from '../../hooks/useLocation';
import * as ImagePicker from 'expo-image-picker';

export function CreateItemScreen(): React.JSX.Element {
  const { colors, isDark } = useTheme();
  const navigation = useNavigation();
  const queryClient = useQueryClient();
  const { latitude, longitude } = useLocation();

  const [titulo, setTitulo] = useState('');
  const [descricao, setDescricao] = useState('');
  const [precoDiaria, setPrecoDiaria] = useState('');
  const [valorCaucao, setValorCaucao] = useState('');
  const [categoriaId, setCategoriaId] = useState<string>('');
  const [fotoUri, setFotoUri] = useState<string | null>(null);

  // Busca categorias na API
  const { data: categorias, isLoading: carregandoCategorias } = useQuery({
    queryKey: ['categorias'],
    queryFn: buscarCategorias,
  });

  const mutation = useMutation({
    mutationFn: async () => {
      // Conversões simples
      const data = {
        titulo,
        descricao,
        preco_diaria: precoDiaria.replace(',', '.'),
        valor_caucao: valorCaucao.replace(',', '.'),
        camada: 'ESSENTIAL', // Default para o MVP
        latitude: latitude || -23.5505, // fallback
        longitude: longitude || -46.6333,
        ...(categoriaId ? { categoria: categoriaId } : {}),
      };
      // O envio da foto precisaria de FormData para a API, mas para o MVP
      // criamos a casca visual perfeita.
      return criarItem(data as any);
    },
    onSuccess: () => {
      Alert.alert('Sucesso', 'Item publicado com sucesso!');
      queryClient.invalidateQueries({ queryKey: ['itens-proximidade'] });
      queryClient.invalidateQueries({ queryKey: ['meus-itens'] });
      navigation.goBack();
    },
    onError: (error: any) => {
      console.error(error);
      Alert.alert('Erro', 'Não foi possível publicar o item. Verifique os dados e tente novamente.');
    },
  });

  const handlePickImage = async () => {
    // Pedir permissão
    const { status } = await ImagePicker.requestMediaLibraryPermissionsAsync();
    if (status !== 'granted') {
      Alert.alert('Permissão necessária', 'Precisamos de acesso à sua galeria para adicionar fotos do item.');
      return;
    }

    const result = await ImagePicker.launchImageLibraryAsync({
      mediaTypes: ImagePicker.MediaTypeOptions.Images,
      allowsEditing: true,
      aspect: [4, 3],
      quality: 0.8,
    });

    if (!result.canceled && result.assets && result.assets.length > 0) {
      setFotoUri(result.assets[0].uri);
    }
  };

  const handleSubmit = () => {
    if (!titulo || !precoDiaria || !valorCaucao || !categoriaId) {
      Alert.alert('Atenção', 'Preencha todos os campos obrigatórios, incluindo a categoria.');
      return;
    }
    mutation.mutate();
  };

  return (
    <SafeAreaView style={[styles.container, { backgroundColor: colors.background }]} edges={['top', 'bottom']}>
      <KeyboardAvoidingView 
        style={styles.flex} 
        behavior={Platform.OS === 'ios' ? 'padding' : undefined}
      >
        <View style={[styles.header, { borderBottomColor: colors.border }]}>
          <Text style={[styles.title, { color: colors.text }]}>Publicar Novo Item</Text>
        </View>

        <ScrollView contentContainerStyle={styles.scrollContent} keyboardShouldPersistTaps="handled">
          
          <TouchableOpacity 
            style={[styles.photoPlaceholder, { backgroundColor: colors.surfaceVariant, borderColor: colors.border }]} 
            onPress={handlePickImage}
            activeOpacity={0.8}
          >
            {fotoUri ? (
              <Image source={{ uri: fotoUri }} style={styles.imagePreview} />
            ) : (
              <>
                <Text style={{ fontSize: 40 }}>📷</Text>
                <Text style={[styles.photoText, { color: colors.textSecondary }]}>Adicionar Foto Principal</Text>
              </>
            )}
          </TouchableOpacity>

          <Input
            label="Título do item *"
            placeholder="Ex: Furadeira Bosch 500W"
            value={titulo}
            onChangeText={setTitulo}
          />

          <View style={styles.section}>
            <Text style={[styles.sectionLabel, { color: colors.text }]}>Categoria *</Text>
            {carregandoCategorias ? (
              <ActivityIndicator size="small" color={BrandColors.primary} />
            ) : (
              <ScrollView horizontal showsHorizontalScrollIndicator={false} contentContainerStyle={styles.categoryScroll}>
                {categorias?.map((cat) => (
                  <TouchableOpacity
                    key={cat.id}
                    style={[
                      styles.categoryChip,
                      { backgroundColor: categoriaId === cat.id ? BrandColors.primary : colors.surface },
                      { borderColor: categoriaId === cat.id ? BrandColors.primary : colors.border }
                    ]}
                    onPress={() => setCategoriaId(cat.id)}
                  >
                    <Text style={[
                      styles.categoryChipText,
                      { color: categoriaId === cat.id ? '#FFFFFF' : colors.text }
                    ]}>
                      {cat.nome}
                    </Text>
                  </TouchableOpacity>
                ))}
              </ScrollView>
            )}
          </View>

          <Input
            label="Descrição"
            placeholder="Detalhes sobre o estado, acessórios..."
            value={descricao}
            onChangeText={setDescricao}
            multiline
            numberOfLines={3}
            inputStyle={{ height: 80 }}
          />

          <View style={styles.row}>
            <View style={styles.half}>
              <Input
                label="Preço da Diária (R$) *"
                placeholder="0.00"
                value={precoDiaria}
                onChangeText={setPrecoDiaria}
                keyboardType="numeric"
              />
            </View>
            <View style={styles.half}>
              <Input
                label="Valor da Caução (R$) *"
                placeholder="0.00"
                value={valorCaucao}
                onChangeText={setValorCaucao}
                keyboardType="numeric"
              />
            </View>
          </View>

        </ScrollView>

        <View style={[styles.footer, { borderTopColor: colors.border, backgroundColor: colors.background }]}>
          <Button 
            title="Cancelar" 
            variant="ghost" 
            onPress={() => navigation.goBack()} 
            style={styles.cancelBtn} 
          />
          <Button 
            title={mutation.isPending ? "Publicando..." : "Publicar Item"} 
            onPress={handleSubmit} 
            disabled={mutation.isPending}
            style={styles.submitBtn} 
          />
        </View>
      </KeyboardAvoidingView>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1 },
  flex: { flex: 1 },
  header: {
    padding: Spacing.md,
    borderBottomWidth: 1,
  },
  title: { ...TextStyles.h2 },
  scrollContent: {
    padding: Spacing.md,
    gap: Spacing.md,
  },
  photoPlaceholder: {
    height: 200,
    borderRadius: BorderRadius.lg,
    alignItems: 'center',
    justifyContent: 'center',
    marginBottom: Spacing.sm,
    borderWidth: 1,
    overflow: 'hidden',
  },
  imagePreview: {
    width: '100%',
    height: '100%',
    resizeMode: 'cover',
  },
  photoText: {
    fontFamily: FontFamily.medium,
    marginTop: Spacing.sm,
  },
  section: {
    marginBottom: Spacing.sm,
  },
  sectionLabel: {
    ...TextStyles.label,
    marginBottom: Spacing.sm,
  },
  categoryScroll: {
    gap: Spacing.sm,
  },
  categoryChip: {
    paddingHorizontal: Spacing.md,
    paddingVertical: Spacing.sm,
    borderRadius: BorderRadius.full,
    borderWidth: 1,
  },
  categoryChipText: {
    fontFamily: FontFamily.medium,
    fontSize: 14,
  },
  row: {
    flexDirection: 'row',
    gap: Spacing.md,
  },
  half: { flex: 1 },
  footer: {
    flexDirection: 'row',
    padding: Spacing.md,
    borderTopWidth: 1,
    gap: Spacing.md,
  },
  cancelBtn: { flex: 1 },
  submitBtn: { flex: 2 },
});

export default CreateItemScreen;
